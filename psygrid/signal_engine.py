"""Signal engine — orchestrates the full decision flow per index:

RAW DATA -> DATA INTEGRITY -> UNDERLYING -> MARKET STRUCTURE -> KEY LEVELS
-> LIQUIDITY -> FUTURES -> OPTIONS -> DEPTH -> INDICATORS -> SETUP
-> CROSS-CONFLUENCE -> STRIKE SELECTION -> RISK -> SIGNAL

Outputs BUY CALL / BUY PUT / WATCH / NO TRADE / DATA GATE BLOCKED /
MARKET CLOSED / WARMING UP for each index. Read-only: no order placement.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import Config, INDICES
from .data_integrity import GateResult, IntegrityGate
from .depth_engine import DepthEngine, DepthState
from .diagnostics import SignalEvaluationTrace, build_trace
from .futures_engine import FuturesEngine, FuturesState
from .indicator_engine import IndicatorEngine, IndicatorState
from .level_engine import LevelEngine, LevelMap
from .liquidity_engine import LiquidityEngine, LiquidityState
from .market_clock import CLOSING, MarketClock, now_ist
from .models import IndexSnapshot, RawResponse
from .option_chain_engine import ChainState, OptionChainEngine
from .risk_engine import RiskEngine
from .schema_adapter import ADAPTERS
from .scoring_engine import LABELS, ScoreResult, ScoringEngine
from .setup_engine import SetupCandidate, SetupEngine
from .signal_state import Signal, SignalEvent, SignalStateManager
from .strike_selector import StrikeSelector
from .structure_engine import StructureEngine, StructureState
from .underlying_engine import UnderlyingTracker

MARK_ORDER = ("structure", "level", "futures", "momentum", "volume", "options", "depth",
              "vwap_indicators", "liquidity")


@dataclass
class Evaluated:
    cand: SetupCandidate
    score: ScoreResult
    selection: object
    plan: object
    plan_error: str
    select_rejections: list[str]


# Entry-state vocabulary: every cycle states explicitly what happened to the
# best detected opportunity, so "nothing found" is never confused with
# "found, but waiting / expired / blocked / suppressed".
NO_SETUP = "NO SETUP"
SETUP_DETECTED = "SETUP DETECTED"                  # below signal grade
RISK_REJECTED = "RISK REJECTED"                    # signal-grade score, no valid risk plan
WAITING_FOR_PULLBACK = "WAITING FOR PULLBACK"
PULLBACK_RECEIVED = "PULLBACK RECEIVED"            # emitted on the pullback this cycle
EXPIRED = "EXPIRED"                                # pullback window ran out: no trade
CANCELLED = "CANCELLED"                            # invalidated / superseded / entries closed
SIGNAL_GRADE_BLOCKED = "SIGNAL-GRADE BUT BLOCKED"  # e.g. entry cutoff
SUPPRESSED = "SUPPRESSED"                          # lifecycle dedup / cooldown
SIGNAL_AUTHORIZED = "SIGNAL AUTHORIZED"
DATA_BLOCKED = "DATA BLOCKED"
NOT_READY = "NOT READY"


@dataclass
class PendingEntry:
    """A pullback-eligible setup found at the end of a burst. It is emitted
    only if price pulls back to ``limit`` before ``expires`` without going
    through the setup's invalidation; otherwise it expires explicitly."""
    evaluated: Evaluated
    armed_ts: datetime
    expires: datetime
    armed_price: float
    extreme: float          # where the burst started (high for PUT, low for CALL); fixed
    impulse: float          # points from `extreme` to `peak` in the signal direction
    limit: float            # underlying price that must be reached to enter
    peak: float = 0.0       # furthest price reached in the signal direction since the burst began

    def __post_init__(self):
        if not self.peak:
            self.peak = self.armed_price

    def track(self, price: float, retrace: float) -> None:
        """A new extreme in the signal direction extends the move being
        retraced; the pullback level stays anchored to the WHOLE move
        (burst start -> furthest point) and never follows price back."""
        s = self.cand.sign
        if (price - self.peak) * s > 0:
            self.peak = price
            self.impulse = (self.peak - self.extreme) * s
            self.limit = round(self.peak - s * retrace * self.impulse, 2)

    @property
    def cand(self) -> SetupCandidate:
        return self.evaluated.cand

    @property
    def key(self) -> tuple:
        c = self.cand
        return entry_key(c)

    def describe(self) -> str:
        c = self.cand
        return (f"{c.direction} {c.setup} armed {self.armed_ts:%H:%M:%S} at {self.armed_price:,.2f} after a "
                f"{self.impulse:,.0f}-pt move (peak {self.peak:,.2f}) — entry on pullback to {self.limit:,.2f} until "
                f"{self.expires:%H:%M:%S}; cancelled beyond invalidation {c.invalidation:,.2f}")


def entry_key(c: SetupCandidate) -> tuple:
    return (c.direction, c.setup, c.key_zone.id if c.key_zone else round(c.level_price, 1))


def pullback_eligible(c: SetupCandidate) -> bool:
    """MOMENTUM-family setups (breakout/breakdown + acceptance, momentum
    continuation, VWAP reclaim) are defined by price moving away from the
    level and are protected by the existing chase limit: they always enter
    immediately, so a trend that never pulls back can never lose them.
    Level-anchored setups (retests, reversals at a level, failed breaks,
    sweeps + reclaim, VWAP rejection) have their edge AT the level, so after
    a burst away from it they wait for a pullback instead of chasing."""
    return c.family != "MOMENTUM"


@dataclass
class IndexDecision:
    index: str
    ts: datetime
    status: str       # BUY_CALL | BUY_PUT | SIGNAL_ACTIVE | WATCH | NO_TRADE | DATA_GATE_BLOCKED | MARKET_CLOSED | WARMING_UP
    headline: str
    reasons: list[str] = field(default_factory=list)
    waiting: list[str] = field(default_factory=list)
    gate: Optional[GateResult] = None
    price: Optional[float] = None
    structure: Optional[StructureState] = None
    levels: Optional[LevelMap] = None
    liquidity: Optional[LiquidityState] = None
    futures: Optional[FuturesState] = None
    chain: Optional[ChainState] = None
    depth: Optional[DepthState] = None
    indicators: Optional[IndicatorState] = None
    signal: Optional[Signal] = None          # newly emitted this cycle
    active: Optional[Signal] = None
    best: Optional[Evaluated] = None
    candidates: list[str] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)
    trace: Optional[SignalEvaluationTrace] = None    # see diagnostics.py
    entry_state: str = NO_SETUP
    entry_detail: str = ""
    pending: Optional["PendingEntry"] = None


@dataclass
class CycleResult:
    ref_time: datetime
    phase: str
    decisions: dict[str, IndexDecision]
    events: list[SignalEvent]
    clock_note: Optional[str] = None


def confirmation_marks(sr: ScoreResult, thr: float) -> list[tuple[str, str, str]]:
    out = []
    for k in MARK_ORDER:
        c = sr.components.get(k)
        if c is None:
            continue
        if c.value is None:
            mark = "-"
        elif c.value >= (0.5 if k in ("level", "liquidity") else thr):
            mark = "Y"
        elif c.value <= -thr:
            mark = "N"
        else:
            mark = "~"
        out.append((LABELS[k], mark, c.detail))
    return out


class IndexPipeline:
    def __init__(self, cfg: Config, index: str, clock: MarketClock, gate: IntegrityGate,
                 store_dir: Optional[Path]):
        self.cfg = cfg
        self.index = index
        self.clock = clock
        self.gate = gate
        self.tracker = UnderlyingTracker(index, store_dir, cfg["integrity"]["max_tick_jump_pct"])
        self.structure = StructureEngine(cfg)
        self.levels = LevelEngine(cfg, index)
        self.liquidity = LiquidityEngine(cfg)
        self.futures = FuturesEngine(cfg)
        self.options = OptionChainEngine(cfg, index)
        self.depth = DepthEngine(cfg)
        self.indicators = IndicatorEngine()
        self.setups = SetupEngine(cfg)
        self.selector = StrikeSelector(cfg, index)
        self.scoring = ScoringEngine(cfg)
        self.risk = RiskEngine(cfg)
        self.entry_cfg = cfg["entry"]
        self.pending: Optional[PendingEntry] = None
        self._expired: dict[tuple, datetime] = {}      # entry_key -> expiry time
        self._day: Optional[str] = None

    def _adapt(self, raws: dict[str, RawResponse], ref: datetime) -> IndexSnapshot:
        snap = IndexSnapshot(index=self.index, ref_time=ref, spot=None, chain=None, depth=None,
                             futures=None, indicators=None)
        for feed, attr in (("spot", "spot"), ("options", "chain"), ("depth", "depth"),
                           ("futures", "futures"), ("indicators", "indicators")):
            r = raws.get(feed)
            if r is None or r.payload is None:
                continue
            try:
                model, issues = ADAPTERS[feed](r.payload, self.index)
            except Exception as exc:          # adapter must never take the engine down
                model, issues = None, [f"adapter error: {type(exc).__name__}: {exc}"]
            setattr(snap, attr, model)
            snap.adapter_issues[feed] = issues
        return snap

    @staticmethod
    def _option_ltp_lookup(chain):
        if chain is None:
            return None

        def lookup(sig: Signal):
            q = chain.quote(sig.strike, sig.option_type)
            return q.ltp if q is not None else None
        return lookup

    def run(self, raws: dict[str, RawResponse], ref: datetime, phase: str,
            state: SignalStateManager) -> tuple[IndexDecision, list[SignalEvent]]:
        day = ref.strftime("%Y-%m-%d")
        if self._day != day:
            self._day = day
            self.tracker.load_day(day)
            self.pending = None
            self._expired.clear()
        events: list[SignalEvent] = []
        snap = self._adapt(raws, ref)
        last = self.tracker.last
        gate = self.gate.evaluate(snap, raws, last.price if last else None, last.ts if last else None)
        dec = IndexDecision(index=self.index, ts=ref, status="NO_TRADE", headline="", gate=gate,
                            price=gate.underlying_price)

        if snap.spot is not None and not snap.spot.synthetic:
            self.tracker.update_feed_candles(snap.spot)

        if not self.clock.is_session(ref):
            events += state.track(self.index, None, ref, session_closing=True)
            self.pending = None
            dec.entry_state = NOT_READY
            dec.status, dec.headline = "MARKET_CLOSED", phase
            dec.reasons.append(f"{phase} — no signals outside market hours")
            return dec, events
        if not gate.authorized:
            dec.status, dec.headline = "DATA_GATE_BLOCKED", "TRADING AUTHORIZATION = BLOCKED"
            dec.reasons = gate.reasons
            dec.active = state.active.get(self.index)
            dec.entry_state = DATA_BLOCKED
            if self.pending is not None:
                dec.pending = self.pending
                dec.entry_detail = "still waiting (no entry while data is blocked): " + self.pending.describe()
            return dec, events

        price = gate.underlying_price
        self.tracker.add_observation(gate.underlying_ts, price, gate.underlying_source)
        s_open = self.clock.session_open_dt(ref)
        or_end = self.clock.opening_range_end(ref)
        mf = self.cfg["structure"]["aggregate_min_fill"]
        bars1 = self.tracker.bars_1m(ref)
        bars5 = self.tracker.bars("5m", ref, mf)
        bars15 = self.tracker.bars("15m", ref, mf)
        dec.coverage = self.tracker.coverage(ref, s_open)

        ind_ok = gate.usable("indicators") and gate.feeds["indicators"].state == "OK"
        ind_vwap = snap.indicators.values.get("vwap") if ind_ok and snap.indicators else None
        st = self.structure.analyze(bars1, price, ref, s_open, or_end, bars5, ind_vwap)
        dec.structure = st
        rng = st.avg_range

        fut = self.futures.analyze(snap.futures, gate.usable("futures"), price, rng,
                                   gate.feeds["futures"].reasons)
        chain = self.options.analyze(snap.chain, gate.usable("options"), price)
        depth = self.depth.analyze(snap.depth, gate.depth_mode, chain.atm, chain.step)
        ind = self.indicators.analyze(snap.indicators, ind_ok, price, rng, gate.feeds["indicators"].reasons)
        dec.futures, dec.chain, dec.depth, dec.indicators = fut, chain, depth, ind

        prev_close = snap.indicators.previous_close if snap.indicators and ind_ok else None
        cands, unavailable = self.levels.discover(price, st, bars1, bars5, bars15,
                                                  self.tracker.previous_day_bars(ref), snap.chain,
                                                  fut.levels, prev_close, ref)
        lm = self.levels.update(price, ref, cands, [b for b in bars1 if b.complete], rng, unavailable, st.vwap)
        dec.levels = lm
        liq = self.liquidity.analyze(bars1, st, lm.zones, price, or_end)
        dec.liquidity = liq

        events += state.track(self.index, price, ref, session_closing=phase == CLOSING,
                              option_ltp=self._option_ltp_lookup(snap.chain if gate.usable("options") else None))
        dec.active = state.active.get(self.index)

        if not st.ready:
            dec.entry_state = NOT_READY
            dec.status, dec.headline = "WARMING_UP", "BUILDING MARKET STRUCTURE"
            dec.reasons.append(st.reason)
            return dec, events

        res = self.setups.detect(price, ref, st, lm, liq, bars1)
        dec.waiting = res.waiting
        dec.candidates = list(res.rejected)

        evaluated: list[Evaluated] = []
        done = [b for b in bars1 if b.complete]
        for c in res.candidates:
            sr = self.selector.select(c.direction, chain, price)
            comps = self.scoring.components(c, st, fut, chain, depth, ind, gate, sr.selection, done)
            score = self.scoring.score(comps)
            plan, err = (None, "no eligible contract")
            if sr.selection is not None:
                plan, err = self.risk.plan(c, sr.selection, lm, price, self.clock.minutes_to_close(ref))
            evaluated.append(Evaluated(c, score, sr.selection, plan, err, sr.rejected))
            dec.candidates.append(f"{c.direction} {c.setup} @ {c.level_price:,.0f}: Q{score.score:.0f} "
                                  f"{score.grade}" + (f" ({'; '.join(score.reasons)})" if score.reasons else "")
                                  + (f" [risk: {err}]" if plan is None else ""))

        # Score/risk every detected candidate - and build its trace - BEFORE
        # the entry-cutoff check below, even though a candidate found during
        # LATE session can never be authorized. Otherwise a genuinely
        # detected, scored setup found in the 15:00-15:20 window would
        # return with dec.trace=None, indistinguishable from "nothing was
        # found" (see docs/SIGNAL_PIPELINE_AUDIT.md's pre-scoring starvation
        # audit). This is pure computation with no side effects - it never
        # calls state.consider()/_build_signal(), so it cannot authorize or
        # register a signal; only the entries_allowed check below decides
        # that, exactly as before.
        tradable: list[Evaluated] = []
        best: Optional[Evaluated] = None
        if evaluated:
            evaluated.sort(key=lambda e: -e.score.score)
            tradable = [e for e in evaluated if e.score.grade == "SIGNAL" and e.plan is not None]
            best = tradable[0] if tradable else evaluated[0]
            dec.best = best
            dec.trace = build_trace(self.index, best.cand, best.score, gate, self.cfg, plan_error=best.plan_error)
        else:
            dec.trace = build_trace(self.index, None, None, gate, self.cfg)

        if not self.clock.entries_allowed(ref):
            if self.pending is not None:
                dec.reasons.append(f"pullback entry cancelled: new entries disabled ({phase}) — "
                                   + self.pending.describe())
                self.pending = None
            if tradable:
                dec.entry_state, dec.entry_detail = SIGNAL_GRADE_BLOCKED, f"new entries disabled ({phase})"
            else:
                dec.entry_state = SETUP_DETECTED if evaluated else NO_SETUP
            dec.status, dec.headline = ("SIGNAL_ACTIVE", "SIGNAL ACTIVE") if dec.active else ("NO_TRADE", "NO TRADE")
            dec.reasons.append(f"{phase}: new entries disabled")
            return dec, events

        top = tradable[0] if tradable else None
        if self.pending is not None and self._resolve_pending(price, ref, chain, lm, state, top, dec,
                                                             gate, events):
            return dec, events

        if top is not None:
            c = top.cand
            eligible = pullback_eligible(c)
            if eligible and self._location_lost(c, ref, dec):
                return dec, events
            burst = self._burst(c.sign, price, bars1, st.avg_range)
            p = self.pending
            if eligible and p is not None and p.cand.direction == c.direction:
                # same-direction level-anchored opportunity while one is already
                # waiting: the waiting entry already tracks new extremes (see
                # PendingEntry.track); this can never bypass the pullback just
                # because the burst went flat, nor restart its deadline
                self._show_waiting(dec)
                return dec, events
            if eligible and burst is not None and self._arm(top, burst, price, ref, st.avg_range, dec):
                return dec, events
            if p is not None:
                dec.reasons.append(f"pullback entry superseded by {c.direction} {c.setup} "
                                   f"({'immediate-entry setup' if not eligible else 'not extended'}): "
                                   + p.describe())
                self.pending = None
            self._emit(top, gate, state, ref, dec, events)
            return dec, events

        if self.pending is not None:
            self._show_waiting(dec)
            return dec, events

        if not evaluated:
            if dec.entry_state not in (EXPIRED, CANCELLED):
                dec.entry_state = NO_SETUP
            dec.status = "SIGNAL_ACTIVE" if dec.active else "NO_TRADE"
            dec.headline = "SIGNAL ACTIVE" if dec.active else "NO TRADE"
            dec.reasons.append("no valid setup at a meaningful level")
            return dec, events

        if dec.entry_state not in (EXPIRED, CANCELLED):
            dec.entry_state = RISK_REJECTED if best.score.grade == "SIGNAL" else SETUP_DETECTED
            if dec.entry_state == RISK_REJECTED:
                dec.entry_detail = best.plan_error
        if best.score.grade in ("SIGNAL", "WATCH"):
            dec.status, dec.headline = "WATCH", f"WATCH {best.cand.direction}"
            dec.reasons += best.score.reasons or ([f"risk: {best.plan_error}"] if best.plan is None else [])
        else:
            dec.status = "SIGNAL_ACTIVE" if dec.active else "NO_TRADE"
            dec.headline = "SIGNAL ACTIVE" if dec.active else "NO TRADE"
            dec.reasons += best.score.reasons
        return dec, events

    # ------------------------------------------------------ pullback entries
    def _burst(self, sign: int, price: float, bars1: list, rng: Optional[float]) -> Optional[tuple[float, float]]:
        """(extreme, impulse) when price has just run more than
        max_impulse_ranges x avg range in the signal direction over the last
        impulse_bars 1m bars (the current, incomplete bar included)."""
        n = self.entry_cfg["impulse_bars"]
        recent = bars1[-n:]
        if not recent or not rng:
            return None
        extreme = max(b.high for b in recent) if sign < 0 else min(b.low for b in recent)
        impulse = (price - extreme) * sign
        if impulse > self.entry_cfg["max_impulse_ranges"] * rng:
            return extreme, impulse
        return None

    def _arm(self, top: Evaluated, burst: tuple[float, float], price: float, ref: datetime,
             rng: float, dec: IndexDecision) -> bool:
        """Put a burst-extended, pullback-eligible setup into WAITING FOR
        PULLBACK with a fixed deadline. Returns False when no pullback entry makes sense - the
        pullback level would lie at/beyond the invalidation, i.e. the stop is
        already close and the entry is not over-extended - so the caller
        emits immediately."""
        c = top.cand
        extreme, impulse = burst
        limit = round(price - c.sign * self.entry_cfg["pullback_retrace"] * impulse, 2)
        if (limit - c.invalidation) * c.sign <= 0:
            return False
        window = timedelta(minutes=self.entry_cfg["pullback_valid_minutes"])
        dec.status, dec.headline = "WATCH", f"WATCH {c.direction} (PULLBACK ENTRY)"
        self.pending = PendingEntry(evaluated=top, armed_ts=ref, expires=ref + window, armed_price=price,
                                    extreme=extreme, impulse=impulse, limit=limit)
        dec.entry_state, dec.entry_detail, dec.pending = WAITING_FOR_PULLBACK, self.pending.describe(), self.pending
        dec.reasons.append(f"no chasing: price ran {impulse:,.0f} pts ({impulse / rng:.1f} avg ranges) "
                           f"in the last {self.entry_cfg['impulse_bars']} min")
        dec.reasons.append(self.pending.describe())
        return True

    def _show_waiting(self, dec: IndexDecision) -> None:
        p = self.pending
        dec.status, dec.headline = "WATCH", f"WATCH {p.cand.direction} (PULLBACK ENTRY)"
        dec.entry_state, dec.entry_detail, dec.pending = WAITING_FOR_PULLBACK, p.describe(), p
        dec.reasons.append(p.describe())

    def _location_lost(self, c: SetupCandidate, ref: datetime, dec: IndexDecision) -> bool:
        """The same level-anchored opportunity already waited a full window and
        price never came back: its entry location is gone, so it is neither
        re-armed nor chased for reentry_block_minutes. Reported explicitly."""
        expired_at = self._expired.get(entry_key(c))
        if expired_at is None or ref - expired_at > timedelta(minutes=self.entry_cfg["reentry_block_minutes"]):
            return False
        dec.status, dec.headline = "NO_TRADE", "NO TRADE"
        dec.entry_state = EXPIRED
        dec.entry_detail = (f"{c.direction} {c.setup}: pullback window expired at {expired_at:%H:%M:%S} "
                            f"without a pullback — entry location lost, not chased")
        dec.reasons.append(dec.entry_detail)
        return True

    def _resolve_pending(self, price: float, ref: datetime, chain, lm, state: SignalStateManager,
                         top: Optional[Evaluated], dec: IndexDecision, gate: GateResult,
                         events: list) -> bool:
        """Advance the waiting entry by one cycle. Returns True when the cycle's
        decision is final (a signal was emitted or suppressed)."""
        p = self.pending
        c = p.cand

        def end(state_name: str, why: str) -> bool:
            self.pending = None
            dec.entry_state, dec.entry_detail = state_name, why
            dec.reasons.append(why)
            return False

        act = state.active.get(self.index)
        if act is not None and act.direction == c.direction:
            return end(CANCELLED, f"pullback entry cancelled: a {act.direction} signal is already active")
        if top is not None and top.cand.direction != c.direction:
            return end(CANCELLED, f"pullback entry cancelled: superseded by a {top.cand.direction} "
                                  f"{top.cand.setup} signal")
        if (price - c.invalidation) * c.sign <= 0:
            return end(CANCELLED, f"pullback entry cancelled: price {price:,.2f} went through invalidation "
                                  f"{c.invalidation:,.2f} before the pullback entry")
        p.track(price, self.entry_cfg["pullback_retrace"])
        if ref > p.expires:
            self._expired[p.key] = ref
            return end(EXPIRED, f"pullback entry expired: {c.direction} {c.setup} never pulled back to "
                                f"{p.limit:,.2f} by {p.expires:%H:%M:%S} — no trade (no chasing)")
        if (price - p.limit) * c.sign > 0:
            return False                                   # still waiting
        sr = self.selector.select(c.direction, chain, price)
        if sr.selection is None:
            dec.reasons.append("pullback reached but no eligible contract this cycle — still waiting")
            return False
        plan, err = self.risk.plan(c, sr.selection, lm, price, self.clock.minutes_to_close(ref))
        if plan is None:
            dec.reasons.append(f"pullback reached but risk plan rejected: {err} — still waiting")
            return False
        self.pending = None
        filled = Evaluated(c, p.evaluated.score, sr.selection, plan, err, sr.rejected)
        note = (f"Entered on pullback to {price:,.2f} (armed {p.armed_ts:%H:%M:%S} at {p.armed_price:,.2f} "
                f"after a {p.impulse:,.0f}-pt burst)")
        self._emit(filled, gate, state, ref, dec, events, note=note, received=True)
        return True

    def _emit(self, e: Evaluated, gate: GateResult, state: SignalStateManager, ref: datetime,
              dec: IndexDecision, events: list, note: Optional[str] = None, received: bool = False) -> bool:
        signal = self._build_signal(e, gate, state, ref)
        if note:
            signal.evidence.insert(0, note)
        ok, why, evs = state.consider(signal, ref)
        events += evs
        if ok:
            dec.signal = dec.active = signal
            dec.status = "BUY_CALL" if signal.direction == "CALL" else "BUY_PUT"
            dec.headline = f"BUY {signal.direction}"
            dec.entry_state = PULLBACK_RECEIVED if received else SIGNAL_AUTHORIZED
            dec.entry_detail = note or f"{signal.setup} entered immediately"
            return True
        dec.active = state.active.get(self.index)
        dec.reasons.append(why)
        dec.entry_state, dec.entry_detail = SUPPRESSED, why
        dec.status = "SIGNAL_ACTIVE" if dec.active else "NO_TRADE"
        dec.headline = "SIGNAL ACTIVE" if dec.active else "NO TRADE"
        return False

    def _build_signal(self, e: Evaluated, gate: GateResult, state: SignalStateManager, now: datetime) -> Signal:
        c, sel, plan, sr = e.cand, e.selection, e.plan, e.score
        z = c.key_zone
        return Signal(
            id=state.new_id(self.index, now), index=self.index, direction=c.direction,
            strike=sel.strike, option_type=sel.option_type, setup=c.setup,
            key_level_id=z.id if z else None, key_level_price=z.center if z else c.level_price,
            level_type=z.role_label if z else "STRUCTURAL LEVEL",
            level_strength=z.strength if z else None, market_state=c.market_state,
            underlying=gate.underlying_price, underlying_source=gate.underlying_source,
            option_ltp=sel.ltp, bid=sel.bid, ask=sel.ask, spread_pct=sel.spread_pct,
            entry_low=plan.entry_low, entry_high=plan.entry_high,
            invalidation=plan.underlying_invalidation, t1=plan.underlying_t1, t2=plan.underlying_t2,
            option_invalidation=plan.option_invalidation, option_t1=plan.option_t1, option_t2=plan.option_t2,
            reward_risk=plan.reward_risk, target_basis=plan.target_basis, holding=plan.holding,
            max_hold_minutes=plan.max_hold_minutes, score=sr.score, grade=sr.grade,
            confirmations=confirmation_marks(sr, self.cfg["scoring"]["confirm_threshold"]),
            evidence=[e for e in c.evidence if not e.startswith("Level: ")]
            + ([f"Level evidence: {', '.join(z.sources[:6])}"] if z else []),
            strike_reasons=sel.reasons + ([f"alternatives: {'; '.join(sel.alternatives)}"] if sel.alternatives else []),
            notes=plan.notes, created=now,
        )


class PsygridEngine:
    def __init__(self, cfg: Config, client=None, logger=None, indices=INDICES):
        self.cfg = cfg
        self.client = client
        self.logger = logger
        self.clock = MarketClock(cfg)
        self.gate = IntegrityGate(cfg)
        self.state = SignalStateManager(cfg)
        store = None
        if logger is not None and cfg["logging"]["persist_observations"]:
            store = logger.observations_dir()
        self.indices = indices
        self.pipes = {i: IndexPipeline(cfg, i, self.clock, self.gate, store) for i in indices}
        self.recent_events: list[SignalEvent] = []

    def reference_time(self, raws: dict, local_now: datetime) -> tuple[datetime, Optional[str]]:
        """Local IST clock, corrected by the HTTP Date header when they disagree
        (protects freshness checks against a drifting PC clock)."""
        skews = [(r.server_date - r.fetched_at).total_seconds()
                 for feeds in raws.values() for r in feeds.values() if r.server_date is not None]
        if not skews:
            return local_now, None
        skew = statistics.median(skews)
        if abs(skew) > 5:
            note = f"local clock differs from server by {skew:+.0f}s; using server-corrected time"
            return local_now + timedelta(seconds=skew), note
        return local_now, None

    def cycle(self, raws: Optional[dict] = None, local_now: Optional[datetime] = None) -> CycleResult:
        if raws is None:
            raws = self.client.fetch_all(self.indices)
        local_now = local_now or now_ist()
        ref, note = self.reference_time(raws, local_now)
        phase = self.clock.phase(ref)
        decisions: dict[str, IndexDecision] = {}
        events: list[SignalEvent] = []
        for i in self.indices:
            try:
                dec, evs = self.pipes[i].run(raws.get(i, {}), ref, phase, self.state)
            except Exception as exc:     # isolate failures per index; never emit on error
                dec = IndexDecision(index=i, ts=ref, status="DATA_GATE_BLOCKED",
                                    headline="ENGINE ERROR — BLOCKED",
                                    reasons=[f"{type(exc).__name__}: {exc}"])
                evs = []
                if self.logger:
                    self.logger.log.exception("pipeline error for %s", i)
            decisions[i] = dec
            events += evs
        self.recent_events = (self.recent_events + events)[-50:]
        if self.logger:
            self._log(raws, ref, decisions, events)
        return CycleResult(ref, phase, decisions, events, note)

    # ------------------------------------------------------------------ logs
    def _log(self, raws, ref, decisions, events) -> None:
        lg = self.logger
        lg.raw(raws, ref)
        for i, d in decisions.items():
            g = d.gate
            if g is not None:
                bad = {f: {"state": fc.state, "reasons": fc.reasons, "http": fc.http_status, "age": fc.age_seconds}
                       for f, fc in g.feeds.items() if fc.state != "OK"}
                if bad or g.reasons:
                    lg.write("data_quality", {"ts": ref, "index": i, "authorization": g.authorization,
                                              "reasons": g.reasons, "feeds": bad}, ref)
            rec = {"ts": ref, "index": i, "status": d.status, "headline": d.headline, "price": d.price,
                   "entry_state": d.entry_state, "entry_detail": d.entry_detail,
                   "reasons": d.reasons, "waiting": d.waiting, "candidates": d.candidates,
                   "underlying_source": g.underlying_source if g else None,
                   "data_quality": g.data_quality if g else None, "coverage": d.coverage}
            if d.structure:
                s = d.structure
                rec["structure"] = {"ready": s.ready, "trend": s.trend, "momentum": s.momentum,
                                    "avg_range": s.avg_range, "vwap": s.vwap, "vwap_source": s.vwap_source,
                                    "or": [s.or_low, s.or_high, s.or_complete],
                                    "session": [s.session_low, s.session_high], "bars": s.bars}
            if d.levels:
                rec["levels"] = [{"id": z.id, "low": round(z.low, 2), "high": round(z.high, 2),
                                  "strength": z.strength, "tier": z.tier, "kind": z.kind, "state": z.state,
                                  "sources": z.sources[:6]} for z in d.levels.zones if z.tier <= 2]
                rec["relations"] = d.levels.relations
            if d.best:
                rec["best"] = {"direction": d.best.cand.direction, "setup": d.best.cand.setup,
                               "score": d.best.score.score, "grade": d.best.score.grade,
                               "components": {k: [c.value, c.detail] for k, c in d.best.score.components.items()},
                               "confirmations": d.best.score.confirmations,
                               "conflicts": d.best.score.conflicts, "plan_error": d.best.plan_error}
            lg.write("decisions", rec, ref)
            if d.signal:
                lg.write("signals", d.signal, ref)
                lg.info(f"SIGNAL {d.signal.index} BUY {d.signal.direction} {d.signal.strike} "
                        f"{d.signal.option_type} Q{d.signal.score}")
        for e in events:
            lg.write("events", e, ref)

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

    def run(self, raws: dict[str, RawResponse], ref: datetime, phase: str,
            state: SignalStateManager) -> tuple[IndexDecision, list[SignalEvent]]:
        day = ref.strftime("%Y-%m-%d")
        if self._day != day:
            self._day = day
            self.tracker.load_day(day)
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
            dec.status, dec.headline = "MARKET_CLOSED", phase
            dec.reasons.append(f"{phase} — no signals outside market hours")
            return dec, events
        if not gate.authorized:
            dec.status, dec.headline = "DATA_GATE_BLOCKED", "TRADING AUTHORIZATION = BLOCKED"
            dec.reasons = gate.reasons
            dec.active = state.active.get(self.index)
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

        events += state.track(self.index, price, ref, session_closing=phase == CLOSING)
        dec.active = state.active.get(self.index)

        if not st.ready:
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
            dec.status, dec.headline = ("SIGNAL_ACTIVE", "SIGNAL ACTIVE") if dec.active else ("NO_TRADE", "NO TRADE")
            dec.reasons.append(f"{phase}: new entries disabled")
            return dec, events

        if not evaluated:
            dec.status = "SIGNAL_ACTIVE" if dec.active else "NO_TRADE"
            dec.headline = "SIGNAL ACTIVE" if dec.active else "NO TRADE"
            dec.reasons.append("no valid setup at a meaningful level")
            return dec, events

        if tradable:
            signal = self._build_signal(best, gate, state, ref)
            ok, why, evs = state.consider(signal, ref)
            events += evs
            if ok:
                dec.signal = dec.active = signal
                dec.status = "BUY_CALL" if signal.direction == "CALL" else "BUY_PUT"
                dec.headline = f"BUY {signal.direction}"
                return dec, events
            dec.active = state.active.get(self.index)
            dec.reasons.append(why)
            dec.status = "SIGNAL_ACTIVE" if dec.active else "NO_TRADE"
            dec.headline = "SIGNAL ACTIVE" if dec.active else "NO TRADE"
            return dec, events
        if best.score.grade in ("SIGNAL", "WATCH"):
            dec.status, dec.headline = "WATCH", f"WATCH {best.cand.direction}"
            dec.reasons += best.score.reasons or ([f"risk: {best.plan_error}"] if best.plan is None else [])
        else:
            dec.status = "SIGNAL_ACTIVE" if dec.active else "NO_TRADE"
            dec.headline = "SIGNAL ACTIVE" if dec.active else "NO TRADE"
            dec.reasons += best.score.reasons
        return dec, events

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

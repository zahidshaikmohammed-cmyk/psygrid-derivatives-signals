"""Setup detection — context-aware and direction-symmetric.

The engine first asks WHERE price is (levels and their states) and WHAT price
is doing there (events: rejection, break, acceptance, failure, retest, sweep),
then maps the event onto a named setup. Every detector is written once with a
direction sign so CALL and PUT logic are mirror images by construction.

Setups
    SUPPORT BOUNCE / RESISTANCE REJECTION
    LIQUIDITY SWEEP + RECLAIM
    BREAKOUT + ACCEPTANCE / BREAKDOWN + ACCEPTANCE
    BREAKOUT + RETEST / BREAKDOWN + RETEST
    FAILED BREAKOUT / FAILED BREAKDOWN
    RANGE EXTREME REVERSAL
    VWAP RECLAIM / VWAP REJECTION
    MULTI-FACTOR LEVEL REACTION
    MOMENTUM CONTINUATION
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .config import Config
from .level_engine import LevelMap, Zone
from .liquidity_engine import LiquidityState
from .models import Candle
from .structure_engine import StructureState, contiguous_tail

BASE_QUALITY = {
    "BREAKOUT + RETEST": 0.90, "BREAKDOWN + RETEST": 0.90,
    "LIQUIDITY SWEEP + RECLAIM": 0.85, "MULTI-FACTOR LEVEL REACTION": 0.85,
    "BREAKOUT + ACCEPTANCE": 0.80, "BREAKDOWN + ACCEPTANCE": 0.80,
    "FAILED BREAKOUT": 0.80, "FAILED BREAKDOWN": 0.80,
    "SUPPORT BOUNCE": 0.70, "RESISTANCE REJECTION": 0.70,
    "RANGE EXTREME REVERSAL": 0.65, "MOMENTUM CONTINUATION": 0.65,
    "VWAP RECLAIM": 0.60, "VWAP REJECTION": 0.60,
}
FAMILY = {
    "MOMENTUM CONTINUATION": "MOMENTUM", "BREAKOUT + ACCEPTANCE": "MOMENTUM",
    "BREAKDOWN + ACCEPTANCE": "MOMENTUM", "VWAP RECLAIM": "MOMENTUM",
    "BREAKOUT + RETEST": "BREAKOUT", "BREAKDOWN + RETEST": "BREAKOUT",
}


@dataclass
class SetupCandidate:
    direction: str                     # CALL | PUT
    setup: str
    key_zone: Optional[Zone]
    level_price: float
    invalidation: float                # underlying price
    quality: float                     # 0..1
    market_state: str
    evidence: list[str] = field(default_factory=list)
    event_ts: Optional[datetime] = None

    @property
    def sign(self) -> int:
        return 1 if self.direction == "CALL" else -1

    @property
    def family(self) -> str:
        return FAMILY.get(self.setup, "REVERSAL")


@dataclass
class SetupResult:
    candidates: list[SetupCandidate]
    rejected: list[str]                # candidates filtered by context, with reason
    waiting: list[str]                 # what the engine is waiting for


def _dir(sign: int) -> str:
    return "CALL" if sign > 0 else "PUT"


class SetupEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["setups"]

    def detect(self, price: float, now: datetime, st: StructureState, lm: LevelMap,
               liq: LiquidityState, bars: list[Candle]) -> SetupResult:
        res = SetupResult([], [], [])
        if not st.ready or st.avg_range is None:
            res.waiting.append(st.reason or "structure not ready")
            return res
        rng = st.avg_range
        buf = self.c["invalidation_buffer_ranges"] * rng
        max_age = self.c["max_event_age_seconds"]
        done = contiguous_tail([b for b in bars if b.complete])
        last = done[-1] if done else None
        cands: list[SetupCandidate] = []

        for z in lm.zones:
            if z.tier > 2:
                continue
            evs = z.recent_events(now, max_age, ("REJECTED", "ACCEPTED", "RECLAIMED", "FAILED_BREAKOUT",
                                                  "FAILED_BREAKDOWN", "RETEST_HELD"))
            if not evs:
                continue
            ev = evs[-1]
            sign = 1 if ev.direction == "UP" else -1
            age = (now - ev.ts).total_seconds()
            fresh = 1 - 0.3 * age / max_age
            src = ", ".join(z.sources[:3])
            beyond_ok = (price > z.high) if sign > 0 else (price < z.low)
            if not beyond_ok:
                continue
            ext = z.distance(price)
            if ext > self.c["max_chase_ranges"] * rng:
                # Pre-scoring starvation audit: every event kind here must be
                # observable when chase-limited, not just ACCEPTED/RECLAIMED/
                # RETEST_HELD - a level engine that HAS detected e.g. a
                # FAILED_BREAKOUT must never disappear with zero trace (no
                # waiting message, no rejected message, no SetupCandidate at
                # all) just because price has since moved further. The gate
                # itself (no chasing) is unchanged; this only makes the
                # rejection visible.
                res.waiting.append(f"{z.center:,.0f} {ev.event.lower().replace('_', ' ')} but price extended "
                                   f"{ext:.0f} pts — waiting for RETEST (no chasing)")
                continue
            edge_inv = (z.low - buf) if sign > 0 else (z.high + buf)

            if ev.event == "RETEST_HELD" and z.accepted_dir == ev.direction:
                name = "BREAKOUT + RETEST" if sign > 0 else "BREAKDOWN + RETEST"
                cands.append(self._mk(name, sign, z, edge_inv, fresh, now, ev.ts,
                                      "RETEST HELD — " + ("ACCEPTANCE ABOVE LEVEL" if sign > 0 else "ACCEPTANCE BELOW LEVEL"),
                                      [f"Level: {src}", "Breakout accepted" if sign > 0 else "Breakdown accepted",
                                       "Retest held"]))
            elif ev.event in ("ACCEPTED", "RECLAIMED"):
                sweep = next((s for s in liq.sweeps if s.ref_zone_id == z.id
                              and (s.direction == "BULLISH") == (sign > 0)), None)
                if ev.event == "RECLAIMED" and sweep:
                    name = "LIQUIDITY SWEEP + RECLAIM"
                    inv = (sweep.extreme - buf) if sign > 0 else (sweep.extreme + buf)
                else:
                    name = "BREAKOUT + ACCEPTANCE" if sign > 0 else "BREAKDOWN + ACCEPTANCE"
                    inv = edge_inv
                cands.append(self._mk(name, sign, z, inv, fresh, now, ev.ts,
                                      ("ACCEPTANCE ABOVE LEVEL" if sign > 0 else "ACCEPTANCE BELOW LEVEL"),
                                      [f"Level: {src}", f"{ev.event.title()} ({ev.note})"]))
            elif ev.event in ("FAILED_BREAKOUT", "FAILED_BREAKDOWN"):
                name = "FAILED BREAKOUT" if ev.event == "FAILED_BREAKOUT" else "FAILED BREAKDOWN"
                ext = z.break_extreme
                inv = ((ext if ext is not None else z.high) + buf) if sign < 0 else \
                      ((ext if ext is not None else z.low) - buf)
                cands.append(self._mk(name, sign, z, inv, fresh, now, ev.ts,
                                      "FAILED BREAKOUT — BACK BELOW LEVEL" if sign < 0 else
                                      "FAILED BREAKDOWN — BACK ABOVE LEVEL",
                                      [f"Level: {src}", "Break could not be accepted", ev.note]))
            elif ev.event == "REJECTED" and not ev.note:
                if last is None or (last.close - last.open) * sign <= 0:
                    res.waiting.append(f"{z.center:,.0f} reaction seen — waiting for a confirming close")
                    continue
                cats = [f for f in z.families if f != "ROUND"]
                if len(cats) >= self.c["multi_factor_min_categories"] and z.strength >= self.c["multi_factor_min_strength"]:
                    name = "MULTI-FACTOR LEVEL REACTION"
                elif st.consolidation and st.range_low is not None and (
                        (sign > 0 and z.low <= st.range_low <= z.high + rng) or
                        (sign < 0 and z.low - rng <= st.range_high <= z.high)):
                    name = "RANGE EXTREME REVERSAL"
                elif cats == ["VWAP"]:
                    name = "VWAP REJECTION"
                else:
                    name = "SUPPORT BOUNCE" if sign > 0 else "RESISTANCE REJECTION"
                cands.append(self._mk(name, sign, z, edge_inv, fresh, now, ev.ts,
                                      "BOUNCING FROM SUPPORT" if sign > 0 else "REJECTING RESISTANCE",
                                      [f"Level: {src}", f"Tested {z.tests}x, rejected {z.rejections}x",
                                       "Confirming close"]))

        # liquidity sweeps (bar based)
        for s in liq.sweeps:
            sign = 1 if s.direction == "BULLISH" else -1
            if any(c.setup == "LIQUIDITY SWEEP + RECLAIM" and c.sign == sign for c in cands):
                continue
            z = next((z for z in lm.zones if z.id == s.ref_zone_id), None)
            inv = (s.extreme - buf) if sign > 0 else (s.extreme + buf)
            fresh = 1 - 0.3 * min(1.0, s.age_bars / max(1, 6))
            cands.append(self._mk("LIQUIDITY SWEEP + RECLAIM", sign, z, inv, fresh, now, s.confirm_ts,
                                  "SWEEP BELOW LEVEL + RECLAIM" if sign > 0 else "SWEEP ABOVE LEVEL + REJECTION",
                                  [f"Swept {s.ref_label} to {s.extreme:,.1f}",
                                   "Closed back " + ("above" if sign > 0 else "below"), "Reclaim holding"],
                                  level_price=s.ref_price))

        # VWAP reclaim / rejection
        if st.vwap is not None and len(done) >= 4:
            cands += self._vwap(price, st, done, buf, now)

        # momentum continuation
        for sign in (1, -1):
            trend_ok = st.trend == ("UP" if sign > 0 else "DOWN")
            mom_ok = st.momentum * sign >= 1.0
            vwap_ok = st.vwap is None or (price - st.vwap) * sign > 0
            if trend_ok and mom_ok and st.expansion and vwap_ok:
                sw = st.swing_lows if sign > 0 else st.swing_highs
                if not sw:
                    continue
                inv = sw[-1].price - buf if sign > 0 else sw[-1].price + buf
                ev = ["Higher highs + higher lows" if sign > 0 else "Lower highs + lower lows",
                      f"Momentum {st.momentum:+.1f} ranges with range expansion"]
                if st.vwap is not None:
                    ev.append("Price " + ("above" if sign > 0 else "below") + " VWAP")
                cands.append(self._mk("MOMENTUM CONTINUATION", sign, None, inv, 1.0, now, now,
                                      "TRENDING " + ("UP" if sign > 0 else "DOWN"), ev,
                                      level_price=sw[-1].price))

        # ---- context filter: never buy straight into an unbroken major opposing level
        room = self.c["min_room_ranges"] * rng
        for c in cands:
            if (c.invalidation - price) * c.sign >= 0:
                res.rejected.append(f"{c.direction} {c.setup}: invalidation on wrong side of price")
                continue
            pending = self._pending_break(lm, price, c, room)
            if pending is not None:
                res.rejected.append(f"{c.direction} {c.setup} held back: break of {pending.center:,.0f} not accepted")
                res.waiting.append(f"{'BREAKOUT' if pending.break_dir == 'UP' else 'BREAKDOWN'} at "
                                   f"{pending.center:,.0f} — WAIT FOR ACCEPTANCE ({pending.closes_beyond} closes so far)")
                continue
            block = self._opposing(lm, price, c, room)
            if block is not None:
                side = "RESISTANCE" if c.sign > 0 else "SUPPORT"
                res.rejected.append(f"{c.direction} {c.setup} blocked: major {side} {block.center:,.0f} "
                                    f"only {block.distance(price):.0f} pts away")
                res.waiting.append(f"PRICE NEAR MAJOR {side} {block.center:,.0f} ({block.id}) — waiting for "
                                   + ("BREAKOUT + ACCEPTANCE or REJECTION + BEARISH CONFIRMATION" if c.sign > 0
                                      else "BREAKDOWN + ACCEPTANCE or BOUNCE + BULLISH CONFIRMATION"))
                continue
            res.candidates.append(c)

        res.waiting += self._waiting(lm, price, st)
        res.waiting = list(dict.fromkeys(res.waiting))
        return res

    # --------------------------------------------------------------- helpers
    def _mk(self, name, sign, z, inv, fresh, now, ev_ts, state, evidence, level_price=None) -> SetupCandidate:
        return SetupCandidate(direction=_dir(sign), setup=name, key_zone=z,
                              level_price=level_price if level_price is not None else (z.center if z else 0.0),
                              invalidation=inv, quality=round(BASE_QUALITY[name] * max(0.5, fresh), 3),
                              market_state=state, evidence=[e for e in evidence if e], event_ts=ev_ts)

    def _vwap(self, price, st, done, buf, now) -> list[SetupCandidate]:
        out = []
        v = st.vwap
        hold = self.c["vwap_hold_closes"]
        touch = self.c["vwap_touch_ranges"] * st.avg_range
        react = st.avg_range
        for sign in (1, -1):
            side = [(b.close - v) * sign > 0 for b in done[-(hold + 1):]]
            if len(side) == hold + 1 and not side[0] and all(side[1:]) and (price - v) * sign > 0:
                out.append(self._mk("VWAP RECLAIM", sign, None, v - sign * buf, 1.0, now, now,
                                    "RECLAIMED VWAP" if sign > 0 else "LOST VWAP",
                                    [f"{hold} closes {'above' if sign > 0 else 'below'} VWAP {v:,.1f} "
                                     f"({st.vwap_source})"], level_price=v))
            recent = done[-3:]
            # price was on the opposite side, probed VWAP and was pushed away in our direction
            if all((b.close - v) * sign > 0 for b in recent) and \
                    any(((b.low if sign > 0 else b.high) - v) * sign <= touch for b in recent) and \
                    (price - v) * sign >= react:
                probe = min(b.low for b in recent) if sign > 0 else max(b.high for b in recent)
                out.append(self._mk("VWAP REJECTION", sign, None, probe - sign * buf, 1.0, now, now,
                                    "HOLDING ABOVE VWAP" if sign > 0 else "REJECTED AT VWAP",
                                    [f"Tested VWAP {v:,.1f} and held", "Moved away by >= 1 range"],
                                    level_price=v))
        return out

    @staticmethod
    def _pending_break(lm: LevelMap, price: float, c: SetupCandidate, room: float) -> Optional[Zone]:
        """A nearby major level broken in the candidate's direction but not yet
        accepted: the engine waits instead of acting on the first break."""
        want = "UP" if c.sign > 0 else "DOWN"
        for z in lm.zones:
            if z.tier <= 2 and z.state == "BROKEN" and z.break_dir == want and z.distance(price) < room:
                return z
        return None

    @staticmethod
    def _opposing(lm: LevelMap, price: float, c: SetupCandidate, room: float) -> Optional[Zone]:
        for z in lm.zones:
            if z.tier > 2 or (c.key_zone is not None and z.id == c.key_zone.id):
                continue
            if c.sign > 0:
                ahead = z.low > price or (z.low <= price <= z.high and z.kind == "RESISTANCE")
                cleared = z.accepted_dir == "UP" and z.state in ("ACCEPTED", "RECLAIMED")
            else:
                ahead = z.high < price or (z.low <= price <= z.high and z.kind == "SUPPORT")
                cleared = z.accepted_dir == "DOWN" and z.state in ("ACCEPTED", "RECLAIMED")
            if ahead and not cleared and z.tier == 1 and z.distance(price) < room:
                return z
        return None

    @staticmethod
    def _waiting(lm: LevelMap, price: float, st: StructureState) -> list[str]:
        out = []
        for z in sorted((z for z in lm.zones if z.tier <= 2), key=lambda z: z.distance(price))[:3]:
            lvl = f"{z.role_label} {z.center:,.0f}"
            if z.state == "APPROACHING":
                if z.kind == "RESISTANCE":
                    out.append(f"APPROACHING {lvl} — waiting for BREAKOUT + ACCEPTANCE or REJECTION + BEARISH CONFIRMATION")
                else:
                    out.append(f"APPROACHING {lvl} — waiting for BREAKDOWN + ACCEPTANCE or BOUNCE + BULLISH CONFIRMATION")
            elif z.state == "TESTING":
                out.append(f"TESTING {lvl} — waiting for acceptance beyond or rejection")
            elif z.state == "BROKEN":
                out.append(f"{'BREAKOUT' if z.break_dir == 'UP' else 'BREAKDOWN'} at {z.center:,.0f} — WAITING FOR "
                           f"ACCEPTANCE ({z.closes_beyond} closes so far)")
        if not out:
            s, r = lm.nearest_support, lm.nearest_resistance
            parts = []
            if s:
                parts.append(f"support {s.center:,.0f} ({lm.dist_support:+.0f})")
            if r:
                parts.append(f"resistance {r.center:,.0f} (+{lm.dist_resistance:.0f})")
            out.append("between levels" + (": " + ", ".join(parts) if parts else "")
                       + f"; structure {st.trend}")
        return out

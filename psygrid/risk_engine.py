"""Risk / invalidation / targets.

Underlying targets come from the next opposing Tier-1/2 zones; when none
exist, R-multiples of the invalidation distance are used and labelled so.
Option prices at invalidation/targets are ESTIMATES from the contract's own
delta and gamma (second-order Taylor): dP = |delta|*dU + 0.5*gamma*dU^2, with dU signed
in the option's favour (gamma convexity cushions adverse moves).
Theta and IV change are ignored; this is stated in the output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .config import Config
from .level_engine import LevelMap
from .setup_engine import SetupCandidate
from .strike_selector import Selection

HOLD = {
    "MOMENTUM": "SHORT INTRADAY MOMENTUM (5-30 min)",
    "BREAKOUT": "INTRADAY CONTINUATION (10-40 min)",
    "REVERSAL": "INTRADAY REVERSAL (15-45 min)",
}


@dataclass
class RiskPlan:
    entry_low: float
    entry_high: float
    underlying_entry: float
    underlying_invalidation: float
    underlying_t1: float
    underlying_t2: float
    target_basis: str
    option_invalidation: Optional[float]
    option_t1: Optional[float]
    option_t2: Optional[float]
    reward_risk: float
    holding: str
    max_hold_minutes: int
    notes: list[str] = field(default_factory=list)


def _tick(x: float, tick: float) -> float:
    return round(round(x / tick) * tick, 2)


def option_estimate(sel: Selection, du: float) -> Optional[float]:
    """Premium change for a favourable underlying move ``du`` (signed in the
    option's favour: + means towards profit)."""
    if sel.delta is None:
        return None
    g = sel.gamma or 0.0
    return abs(sel.delta) * du + 0.5 * g * du * du


class RiskEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["risk"]
        self.hold_cfg = cfg["signal_state"]["max_hold_minutes"]

    def plan(self, cand: SetupCandidate, sel: Selection, lm: LevelMap, price: float,
             minutes_to_close: float) -> tuple[Optional[RiskPlan], str]:
        d = cand.sign
        risk = (price - cand.invalidation) * d
        if risk <= 0:
            return None, "invalidation not on the protective side of price"
        opp = [z for z in lm.zones if z.tier <= 2 and z.id != (cand.key_zone.id if cand.key_zone else None)]
        if d > 0:
            ahead = sorted((z.low for z in opp if z.low > price), key=float)
        else:
            ahead = sorted((z.high for z in opp if z.high < price), key=lambda x: -x)
        min_rr = self.c["min_reward_risk"]
        notes = []
        if ahead:
            t1 = ahead[0]
            if (t1 - price) * d < min_rr * risk:
                return None, (f"insufficient room: next level {t1:,.1f} is {(t1 - price) * d:.1f} pts away, "
                              f"risk {risk:.1f} pts (R:R < {min_rr})")
            t2 = ahead[1] if len(ahead) > 1 else price + d * max(abs(t1 - price) + risk, self.c["r_multiple_t2"] * risk)
            basis = "next key levels"
            if len(ahead) == 1:
                notes.append("T2 = T1 + 1R (no second level)")
        else:
            t1 = price + d * self.c["r_multiple_t1"] * risk
            t2 = price + d * self.c["r_multiple_t2"] * risk
            basis = "R-multiples (no opposing key level mapped)"
        rr = (t1 - price) * d / risk
        tick = self.c["tick"]
        band = max(sel.ltp * self.c["entry_band_pct"] / 100, sel.spread)
        entry_low = _tick(max(tick, sel.ltp - band), tick)
        entry_high = _tick(max(sel.ask, sel.ltp + band), tick)
        o_inv = o_t1 = o_t2 = None
        chg = option_estimate(sel, -risk)
        if chg is not None:
            o_inv = _tick(max(tick, sel.ltp + chg), tick)
            o_t1 = _tick(sel.ltp + option_estimate(sel, abs(t1 - price)), tick)
            o_t2 = _tick(sel.ltp + option_estimate(sel, abs(t2 - price)), tick)
            notes.append("option levels estimated from delta/gamma; theta & IV change ignored")
        else:
            notes.append("option greeks unavailable — manage by underlying levels only")
        fam = cand.family
        hold = self.hold_cfg.get(fam, self.hold_cfg["DEFAULT"])
        if minutes_to_close < hold:
            notes.append(f"only {minutes_to_close:.0f} min to session close")
            hold = max(1, int(minutes_to_close))
        return RiskPlan(entry_low=entry_low, entry_high=entry_high, underlying_entry=price,
                        underlying_invalidation=round(cand.invalidation, 2), underlying_t1=round(t1, 2),
                        underlying_t2=round(t2, 2), target_basis=basis, option_invalidation=o_inv,
                        option_t1=o_t1, option_t2=o_t2, reward_risk=round(rr, 2),
                        holding=HOLD[fam], max_hold_minutes=hold, notes=notes), ""

"""Cross-confluence + Signal Quality Score (0-100).

The score is a CONFLUENCE score, not a probability. It has not been
statistically calibrated; logs/ records every component so it can be
calibrated later on out-of-sample outcomes.

Each component is expressed on -1..+1 *relative to the candidate direction*
(+1 fully supports, -1 fully opposes). Unavailable components contribute 0
but keep their weight in the denominator, so missing data always lowers the
score and is never replaced by a guessed value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .config import Config
from .data_integrity import GateResult
from .depth_engine import DepthState
from .futures_engine import FuturesState
from .indicator_engine import IndicatorState
from .option_chain_engine import ChainState
from .setup_engine import SetupCandidate
from .strike_selector import Selection
from .structure_engine import StructureState

DIRECTIONAL = ("structure", "futures", "momentum", "options", "depth", "vwap_indicators")
INDEPENDENT = ("futures", "options", "depth", "volume", "vwap_indicators")
LABELS = {
    "structure": "Underlying structure", "level": "Key level", "futures": "Futures confirmation",
    "momentum": "Momentum", "volume": "Volume / participation expansion",
    "options": "Option participation", "liquidity": "Contract liquidity", "depth": "Depth confirmation",
    "vwap_indicators": "VWAP / indicators", "setup": "Setup quality", "data_quality": "Data quality",
}


@dataclass
class Component:
    name: str
    value: Optional[float]           # None = unavailable
    detail: str


@dataclass
class ScoreResult:
    score: float
    grade: str                       # SIGNAL | WATCH | NO_TRADE
    components: dict[str, Component]
    confirmations: list[str]
    conflicts: list[str]
    reasons: list[str] = field(default_factory=list)


def _clip(x: float) -> float:
    return max(-1.0, min(1.0, x))


class ScoringEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["scoring"]

    def components(self, cand: SetupCandidate, st: StructureState, fut: FuturesState,
                   chain: ChainState, depth: DepthState, ind: IndicatorState, gate: GateResult,
                   sel: Optional[Selection], recent_bars: list) -> dict[str, Component]:
        d = cand.sign
        comps: dict[str, Component] = {}
        rng = st.avg_range or 1.0

        # structure: swing trend + direction of the latest completed bars
        trend = {"UP": 1.0, "DOWN": -1.0}.get(st.trend, 0.0)
        net = 0.0
        if len(recent_bars) >= 3:
            net = _clip((recent_bars[-1].close - recent_bars[-3].open) / (2 * rng))
        comps["structure"] = Component("structure", _clip(0.5 * trend * d + 0.5 * net * d),
                                       f"trend {st.trend}, {st.high_seq or '-'}/{st.low_seq or '-'}, "
                                       f"last 3 bars {net:+.2f}")
        z = cand.key_zone
        if z is not None:
            comps["level"] = Component("level", z.strength / 100,
                                       f"{z.role_label} {z.center:,.0f} strength {z.strength:.0f}")
        else:
            comps["level"] = Component("level", 0.4, f"structural level {cand.level_price:,.1f}")
        comps["futures"] = Component("futures", None if fut.score is None else fut.score * d,
                                     fut.classification if fut.available else "; ".join(fut.reasons)[:80])
        comps["momentum"] = Component("momentum", _clip(st.momentum * d / 3),
                                      f"{st.momentum:+.2f} ranges ({st.momentum_state})"
                                      + (", expansion" if st.expansion else ""))
        vol_vals, vol_det = [], []
        if chain.activity_expansion is not None:
            vol_vals.append(chain.activity_expansion)
            vol_det.append(f"options activity x{chain.activity_ratio}")
        if ind.available and ind.rvol is not None:
            vol_vals.append(max(0.0, min(1.0, ind.rvol - 1.0)))
            vol_det.append(f"RVOL {ind.rvol:.2f}")
        comps["volume"] = Component("volume", max(vol_vals) if vol_vals else None,
                                    ", ".join(vol_det) or "unavailable (no volume baseline yet)")
        comps["options"] = Component("options", None if chain.participation is None else _clip(chain.participation * d),
                                     ", ".join(f"{k} {v:+.2f}" for k, v in chain.participation_parts.items())
                                     or "building history")
        comps["liquidity"] = Component("liquidity", sel.liquidity if sel else 0.0,
                                       f"{sel.strike:,.0f}{sel.option_type} spread {sel.spread_pct:.2f}%"
                                       if sel else "no eligible contract")
        comps["depth"] = Component("depth", None if depth.score is None else _clip(depth.score * d * 2),
                                   f"{depth.mode}: CE {depth.ce_imbalance:+.2f} / PE {depth.pe_imbalance:+.2f}"
                                   if depth.score is not None else "; ".join(depth.reasons))
        if ind.available and ind.score is not None:
            comps["vwap_indicators"] = Component("vwap_indicators", _clip(ind.score * d), ", ".join(ind.details))
        elif st.vwap is not None:
            comps["vwap_indicators"] = Component("vwap_indicators", _clip((st.vwap_distance or 0) / (2 * rng) * d),
                                                 f"price vs VWAP {st.vwap_distance:+.1f} ({st.vwap_source})")
        else:
            comps["vwap_indicators"] = Component("vwap_indicators", None, "; ".join(ind.reasons)[:80] or "unavailable")
        comps["setup"] = Component("setup", cand.quality, cand.setup)
        comps["data_quality"] = Component("data_quality", gate.data_quality, f"{gate.data_quality:.2f}")
        return comps

    def score(self, comps: dict[str, Component]) -> ScoreResult:
        w = self.c["weights"]
        total = sum(w.values())
        pos = sum(w[k] * max(0.0, c.value) for k, c in comps.items() if c.value is not None)
        neg = sum(w[k] * -c.value for k, c in comps.items()
                  if c.value is not None and c.value < 0 and k in DIRECTIONAL)
        score = 100 * (pos - self.c["conflict_penalty"] * neg) / total
        score = round(max(0.0, min(100.0, score)), 1)
        confirmations = [k for k in INDEPENDENT
                         if comps[k].value is not None and comps[k].value >= self.c["confirm_threshold"]]
        conflicts = [k for k in DIRECTIONAL
                     if comps[k].value is not None and comps[k].value <= self.c["strong_conflict"]]
        res = ScoreResult(score, "NO_TRADE", comps, confirmations, conflicts)
        if len(conflicts) > self.c["max_strong_conflicts"]:
            res.reasons.append("conflicting signals: " + ", ".join(LABELS[k] for k in conflicts))
        elif len(confirmations) < self.c["min_independent_confirmations"]:
            res.reasons.append(f"insufficient independent confirmation ({len(confirmations)}/"
                               f"{self.c['min_independent_confirmations']}: "
                               f"{', '.join(LABELS[k] for k in confirmations) or 'none'})")
        elif score >= self.c["signal_threshold"]:
            res.grade = "SIGNAL"
        elif score >= self.c["watch_threshold"]:
            res.grade = "WATCH"
            res.reasons.append(f"quality {score:.0f} below signal threshold {self.c['signal_threshold']}")
        else:
            res.reasons.append(f"quality {score:.0f} below watch threshold {self.c['watch_threshold']}")
        return res

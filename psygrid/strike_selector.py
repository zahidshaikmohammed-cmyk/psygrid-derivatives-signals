"""Dynamic strike selection. Never picks a contract just because it is ATM:
every eligible contract is scored on delta, spread, liquidity, top-of-book
size, IV relative to its neighbours and premium bounds."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Optional

from .config import Config
from .option_chain_engine import ChainState


@dataclass
class Selection:
    strike: float
    option_type: str
    ltp: float
    bid: float
    ask: float
    spread: float
    spread_pct: float
    delta: Optional[float]
    gamma: Optional[float]
    iv: Optional[float]
    volume: Optional[float]
    oi: Optional[float]
    liquidity: float          # 0..1 contract quality used by scoring
    score: float
    reasons: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)


@dataclass
class SelectionResult:
    selection: Optional[Selection]
    rejected: list[str]


class StrikeSelector:
    def __init__(self, cfg: Config, index: str):
        self.c = cfg["options"]
        self.index = index

    def select(self, direction: str, chain: ChainState, price: float) -> SelectionResult:
        otype = "CE" if direction == "CALL" else "PE"
        if not chain.available or chain.atm is None or chain.step is None:
            return SelectionResult(None, ["option chain unavailable"])
        lo_prem = self.c["min_premium"][self.index]
        hi_prem = self.c["max_premium"][self.index]
        dmin, dmax = self.c["delta_band"]
        maxk = self.c["max_strikes_from_atm"]
        ivs = [cv.quote.iv for (k, t), cv in chain.contracts.items() if t == otype and cv.quote.iv]
        iv_med = median(ivs) if ivs else None
        rejected: list[str] = []
        scored: list[Selection] = []
        for (k, t), cv in chain.contracts.items():
            if t != otype or abs(k - chain.atm) > maxk * chain.step + 1e-6:
                continue
            q = cv.quote
            tag = f"{k:,.0f} {otype}"
            if not cv.accepted:
                rejected.append(f"{tag}: {', '.join(cv.reject_reasons)}")
                continue
            if not (lo_prem <= q.ltp <= hi_prem):
                rejected.append(f"{tag}: premium {q.ltp:.2f} outside [{lo_prem}, {hi_prem}]")
                continue
            if not q.bid_qty or not q.ask_qty:
                rejected.append(f"{tag}: empty top-of-book size")
                continue
            ad = abs(q.delta) if q.delta is not None else None
            if ad is not None and not (dmin <= ad <= dmax):
                rejected.append(f"{tag}: |delta| {ad:.2f} outside [{dmin}, {dmax}]")
                continue
            reasons = []
            # component scores 0..1
            if ad is not None:
                s_delta = max(0.0, 1 - abs(ad - self.c["target_delta"]) / 0.25)
                reasons.append(f"delta {q.delta:+.2f}")
            else:
                # no greeks: fall back to moneyness distance (stated explicitly)
                s_delta = max(0.0, 1 - abs(k - price) / (maxk * chain.step))
                reasons.append("delta unavailable — scored by distance from underlying")
            s_spread = max(0.0, 1 - q.spread_pct / self.c["max_spread_pct"])
            reasons.append(f"spread {q.spread:.2f} ({q.spread_pct:.2f}%)")
            s_liq = cv.liquidity
            reasons.append(f"volume {q.volume / 1e6:.2f}M, OI {q.oi / 1e6:.2f}M")
            s_book = min(1.0, min(q.bid_qty, q.ask_qty) / max(1.0, max(q.bid_qty, q.ask_qty)))
            s_iv = 1.0
            if q.iv and iv_med:
                rel = q.iv / iv_med - 1
                s_iv = max(0.0, 1 - max(0.0, rel) * 4)
                reasons.append(f"IV {q.iv:.1f} (window median {iv_med:.1f})")
            score = 0.30 * s_delta + 0.25 * s_spread + 0.25 * s_liq + 0.10 * s_book + 0.10 * s_iv
            liquidity = round(0.5 * s_spread + 0.35 * s_liq + 0.15 * s_book, 3)
            scored.append(Selection(strike=k, option_type=otype, ltp=q.ltp, bid=q.bid, ask=q.ask,
                                    spread=round(q.spread, 2), spread_pct=round(q.spread_pct, 3),
                                    delta=q.delta, gamma=q.gamma, iv=q.iv, volume=q.volume, oi=q.oi,
                                    liquidity=liquidity, score=round(score, 3), reasons=reasons))
        if not scored:
            return SelectionResult(None, rejected or ["no eligible contract"])
        scored.sort(key=lambda s: -s.score)
        best = scored[0]
        best.alternatives = [f"{s.strike:,.0f} {s.option_type} score {s.score:.2f}" for s in scored[1:3]]
        pos = "ATM" if best.strike == chain.atm else ("ITM" if (best.strike < price) == (otype == "CE") else "OTM")
        best.reasons.insert(0, f"{pos} strike, selection score {best.score:.2f} (best of {len(scored)})")
        return SelectionResult(best, rejected)

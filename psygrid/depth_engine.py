"""Market-depth / microstructure confirmation (never a trigger).

Bullish depth evidence  = near-ATM CE books bid-heavy AND PE books ask-heavy.
Bearish depth evidence  = the mirror image.
Displayed depth is not guaranteed liquidity; a large wall only appears as a
note. In QUOTE_ONLY mode (20-level book unavailable but quote-level
buy/sell totals fresh) the score is halved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median
from typing import Optional

from .config import Config
from .models import DepthData


@dataclass
class DepthState:
    mode: str
    score: Optional[float] = None       # -1..1 bullish positive
    ce_imbalance: Optional[float] = None
    pe_imbalance: Optional[float] = None
    change: Optional[float] = None
    walls: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def imbalance(bid_qty: float, ask_qty: float) -> Optional[float]:
    tot = bid_qty + ask_qty
    return None if tot <= 0 else (bid_qty - ask_qty) / tot


class DepthEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["depth"]
        self.prev_score: Optional[float] = None

    def analyze(self, depth: Optional[DepthData], mode: str, atm: Optional[float],
                step: Optional[float]) -> DepthState:
        if depth is None or mode == "UNAVAILABLE" or atm is None or step is None:
            return DepthState(mode="UNAVAILABLE", reasons=["depth unavailable"])
        near = [c for c in depth.contracts
                if abs(c.strike - atm) <= self.c["strikes_each_side"] * step + 1e-6 and not c.crossed_book]
        if not near:
            return DepthState(mode="UNAVAILABLE", reasons=["no depth contracts near ATM"])
        st = DepthState(mode=mode)
        per = {"CE": [], "PE": []}
        n = self.c["top_levels"]
        for c in near:
            if mode == "FULL" and c.bids and c.asks:
                top = imbalance(sum(l.quantity for l in c.bids[:n]), sum(l.quantity for l in c.asks[:n]))
                full = imbalance(sum(l.quantity for l in c.bids), sum(l.quantity for l in c.asks))
                if top is None or full is None:
                    continue
                per[c.option_type].append(0.6 * top + 0.4 * full)
                qs = [l.quantity for l in c.bids + c.asks]
                med = median(qs) if qs else 0
                for side, lv in (("bid", c.bids), ("ask", c.asks)):
                    for l in lv:
                        if med and l.quantity >= 8 * med:
                            st.walls.append(f"{c.strike:g}{c.option_type} {side} wall {l.quantity:g} @ {l.price}")
            elif c.buy_qty is not None and c.sell_qty is not None:
                imb = imbalance(c.buy_qty, c.sell_qty)
                if imb is not None:
                    per[c.option_type].append(imb)
        if not per["CE"] or not per["PE"]:
            return DepthState(mode="UNAVAILABLE", reasons=["depth missing on one option side"])
        st.ce_imbalance = round(mean(per["CE"]), 3)
        st.pe_imbalance = round(mean(per["PE"]), 3)
        score = (st.ce_imbalance - st.pe_imbalance) / 2
        if mode == "QUOTE_ONLY":
            score *= 0.5
            st.reasons.append("quote-level buy/sell totals only (book unavailable)")
        st.score = round(max(-1.0, min(1.0, score)), 3)
        if self.prev_score is not None:
            st.change = round(st.score - self.prev_score, 3)
        self.prev_score = st.score
        st.walls = st.walls[:3]
        return st

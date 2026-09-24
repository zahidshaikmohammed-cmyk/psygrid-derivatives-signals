"""Futures confirmation. Never a standalone trigger — only a confluence input.

basis = futures_last_price - underlying_price
Classification uses futures momentum measured in underlying average bar
ranges plus the direction of the basis change.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .config import Config
from .models import FuturesData

CLASS_SCORE = {
    "STRONG_BULLISH_CONFIRMATION": 1.0, "BULLISH_CONFIRMATION": 0.6, "NEUTRAL": 0.0,
    "BEARISH_CONFIRMATION": -0.6, "STRONG_BEARISH_CONFIRMATION": -1.0,
}


@dataclass
class FuturesState:
    available: bool
    classification: str = "UNAVAILABLE"
    basis: Optional[float] = None
    basis_change: Optional[float] = None
    momentum: Optional[float] = None       # futures move / underlying avg range
    score: Optional[float] = None          # -1..1 (bullish positive)
    levels: list[tuple[float, str]] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


class FuturesEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["futures"]
        self.hist: deque = deque(maxlen=max(2, self.c["momentum_polls"] + 1))

    def analyze(self, fut: Optional[FuturesData], usable: bool, spot: Optional[float],
                avg_range: Optional[float], block_reasons: list[str]) -> FuturesState:
        if not usable or fut is None or fut.last_price is None or spot is None:
            return FuturesState(available=False, reasons=block_reasons or ["futures feed unavailable"])
        if not self.hist or self.hist[-1][0] != fut.updated_at:
            self.hist.append((fut.updated_at, fut.last_price, spot))
        st = FuturesState(available=True, basis=fut.last_price - spot)

        # spot-equivalent futures levels (converted with the current basis)
        if fut.ohlc:
            for key, label in (("high", "Futures day high"), ("low", "Futures day low")):
                if key in fut.ohlc:
                    st.levels.append((fut.ohlc[key] - st.basis, f"{label} (spot-equiv)"))
        if fut.average_price:
            st.levels.append((fut.average_price - st.basis, "Futures average price (spot-equiv)"))

        if len(self.hist) < 2 or not avg_range:
            st.classification, st.score = "NEUTRAL", 0.0
            st.reasons.append("building futures history")
            return st
        _, f0, s0 = self.hist[0]
        _, f1, s1 = self.hist[-1]
        st.basis_change = (f1 - s1) - (f0 - s0)
        st.momentum = (f1 - f0) / avg_range
        m = st.momentum
        widening_with_move = st.basis_change * m > 0
        if abs(m) >= self.c["strong_ranges"] and widening_with_move:
            st.classification = "STRONG_BULLISH_CONFIRMATION" if m > 0 else "STRONG_BEARISH_CONFIRMATION"
        elif abs(m) >= self.c["confirm_ranges"]:
            st.classification = "BULLISH_CONFIRMATION" if m > 0 else "BEARISH_CONFIRMATION"
        else:
            st.classification = "NEUTRAL"
        st.score = CLASS_SCORE[st.classification]
        st.reasons.append(f"futures move {m:+.2f} ranges, basis {st.basis:+.1f} ({st.basis_change:+.1f})")
        if fut.buy_qty and fut.sell_qty:
            imb = (fut.buy_qty - fut.sell_qty) / (fut.buy_qty + fut.sell_qty)
            st.reasons.append(f"futures buy/sell qty imbalance {imb:+.2f}")
        return st

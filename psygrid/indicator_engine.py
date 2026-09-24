"""Indicator confirmation, using only indicators the feed marks ready.

Indicators never trigger a trade; they are one confluence component. RSI is
read as a momentum regime (above 55 / below 45), not as an overbought /
oversold reversal signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import IndicatorData


@dataclass
class IndicatorState:
    available: bool
    score: Optional[float] = None          # -1..1 bullish positive
    vwap: Optional[float] = None
    rvol: Optional[float] = None
    details: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


class IndicatorEngine:
    def analyze(self, ind: Optional[IndicatorData], usable: bool, price: Optional[float],
                avg_range: Optional[float], block_reasons: list[str]) -> IndicatorState:
        if not usable or ind is None or price is None:
            return IndicatorState(available=False, reasons=block_reasons or ["indicators unavailable"])
        v = ind.values
        st = IndicatorState(available=True, vwap=v.get("vwap"), rvol=v.get("rvol_20"))
        parts: list[float] = []
        if "vwap" in v:
            scale = avg_range or max(price * 0.0005, 1e-9)
            parts.append(max(-1.0, min(1.0, (price - v["vwap"]) / (2 * scale))))
            st.details.append(f"price {'above' if price > v['vwap'] else 'below'} VWAP {v['vwap']:.1f}")
        if "ema_9" in v and "ema_20" in v:
            parts.append(1.0 if v["ema_9"] > v["ema_20"] else -1.0)
            st.details.append(f"EMA9 {'>' if v['ema_9'] > v['ema_20'] else '<'} EMA20")
        if "macd_histogram" in v:
            parts.append(1.0 if v["macd_histogram"] > 0 else -1.0 if v["macd_histogram"] < 0 else 0.0)
            st.details.append(f"MACD hist {v['macd_histogram']:+.2f}")
        if "rsi_14" in v:
            r = v["rsi_14"]
            parts.append(0.5 if r > 55 else -0.5 if r < 45 else 0.0)
            st.details.append(f"RSI {r:.0f}")
        if "plus_di_14" in v and "minus_di_14" in v:
            s = 1.0 if v["plus_di_14"] > v["minus_di_14"] else -1.0
            if v.get("adx_14", 0) < 20:
                s *= 0.5
            parts.append(s)
            st.details.append(f"+DI/-DI {v['plus_di_14']:.0f}/{v['minus_di_14']:.0f}"
                              + (f" ADX {v['adx_14']:.0f}" if "adx_14" in v else ""))
        if parts:
            st.score = round(sum(parts) / len(parts), 3)
        else:
            st.reasons.append("no directional indicator ready")
        if ind.not_ready:
            st.reasons.append(f"not ready: {', '.join(ind.not_ready[:6])}")
        return st

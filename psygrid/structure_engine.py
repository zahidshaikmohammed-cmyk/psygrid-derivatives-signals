"""Underlying market structure: swings, HH/HL/LH/LL, trend, momentum,
consolidation, session extremes, opening range, VWAP distance.

All logic is direction-symmetric: every bullish rule has a mirrored bearish
rule computed by the same code path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Optional

from .config import Config
from .models import Candle


@dataclass
class Swing:
    ts: datetime
    price: float
    kind: str               # H | L
    timeframe: str          # 1m | 5m | 15m | FEED_5m ...


@dataclass
class StructureState:
    ready: bool
    reason: str = ""
    bars: int = 0
    price: Optional[float] = None
    avg_range: Optional[float] = None
    session_high: Optional[float] = None
    session_low: Optional[float] = None
    session_extremes_complete: bool = False
    or_high: Optional[float] = None
    or_low: Optional[float] = None
    or_complete: bool = False
    swings: list[Swing] = field(default_factory=list)
    swing_highs: list[Swing] = field(default_factory=list)
    swing_lows: list[Swing] = field(default_factory=list)
    high_seq: Optional[str] = None           # HH | LH | EH
    low_seq: Optional[str] = None            # HL | LL | EL
    trend: str = "UNKNOWN"                   # UP | DOWN | RANGE | UNKNOWN
    momentum: float = 0.0                    # (close - close_k) / avg_range, signed
    momentum_state: str = "FLAT"
    expansion: bool = False
    consolidation: bool = False
    range_high: Optional[float] = None
    range_low: Optional[float] = None
    vwap: Optional[float] = None
    vwap_source: Optional[str] = None
    vwap_distance: Optional[float] = None
    bar_sources: str = ""
    notes: list[str] = field(default_factory=list)


def find_swings(bars: list[Candle], n: int, timeframe: str) -> list[Swing]:
    """Fractal swings: a high strictly above the ``n`` bars on its left and at
    least equal to the ``n`` bars on its right (first bar of a flat top wins;
    mirrored for lows)."""
    out: list[Swing] = []
    for i in range(n, len(bars) - n):
        left, right = bars[i - n:i], bars[i + 1:i + n + 1]
        h, l = bars[i].high, bars[i].low
        if all(h > b.high for b in left) and all(h >= b.high for b in right):
            out.append(Swing(bars[i].ts, h, "H", timeframe))
        if all(l < b.low for b in left) and all(l <= b.low for b in right):
            out.append(Swing(bars[i].ts, l, "L", timeframe))
    return out


def segments(bars: list[Candle], max_gap_minutes: float = 3.0) -> list[list[Candle]]:
    """Split bars wherever consecutive bars are more than ``max_gap_minutes``
    apart. Swings, momentum and ranges are only computed inside a segment so a
    data gap is never treated as adjacent price action."""
    out: list[list[Candle]] = []
    for b in bars:
        if out and (b.ts - out[-1][-1].ts).total_seconds() <= max_gap_minutes * 60:
            out[-1].append(b)
        else:
            out.append([b])
    return out


def contiguous_tail(bars: list[Candle], max_gap_minutes: float = 3.0) -> list[Candle]:
    segs = segments(bars, max_gap_minutes)
    return segs[-1] if segs else []


def find_swings_segmented(bars: list[Candle], n: int, timeframe: str, max_gap_minutes: float) -> list[Swing]:
    out: list[Swing] = []
    for seg in segments(bars, max_gap_minutes):
        out += find_swings(seg, n, timeframe)
    return out


def _seq(swings: list[Swing], tol: float, up: str, down: str, eq: str) -> Optional[str]:
    if len(swings) < 2:
        return None
    a, b = swings[-2].price, swings[-1].price
    if b > a + tol:
        return up
    if b < a - tol:
        return down
    return eq


def vwap_from_bars(bars: list[Candle]) -> Optional[float]:
    """Typical-price VWAP; only when every bar carries real volume."""
    if not bars or any(b.volume is None for b in bars):
        return None
    vol = sum(b.volume for b in bars)
    if vol <= 0:
        return None
    return sum((b.high + b.low + b.close) / 3 * b.volume for b in bars) / vol


class StructureEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["structure"]

    def analyze(self, bars_1m: list[Candle], price: Optional[float], now: datetime,
                session_open: datetime, or_end: datetime, bars_5m: list[Candle] | None = None,
                indicator_vwap: Optional[float] = None) -> StructureState:
        all_done = [b for b in bars_1m if b.complete]
        done = contiguous_tail(all_done, self.c["max_gap_minutes"])
        st = StructureState(ready=False, bars=len(done), price=price)
        if price is None:
            st.reason = "no underlying price"
            return st
        srcs = sorted({b.source for b in bars_1m})
        st.bar_sources = ", ".join(srcs)

        all_bars = bars_1m
        if all_bars:
            st.session_high = max([b.high for b in all_bars] + [price])
            st.session_low = min([b.low for b in all_bars] + [price])
            st.session_extremes_complete = all_bars[0].ts <= session_open
            if not st.session_extremes_complete:
                st.notes.append(f"session high/low observed from {all_bars[0].ts:%H:%M} only")

        or_bars = [b for b in all_bars if session_open <= b.ts < or_end]
        if or_bars:
            st.or_high = max(b.high for b in or_bars)
            st.or_low = min(b.low for b in or_bars)
            minutes = {b.ts for b in or_bars}
            expected = int((or_end - session_open).total_seconds() // 60)
            st.or_complete = now >= or_end and len(minutes) >= expected * 0.8
            if not st.or_complete:
                st.notes.append(f"opening range incomplete ({len(minutes)}/{expected} bars)")

        # VWAP: indicator feed (already freshness-gated) or computed from feed bars with volume
        if indicator_vwap is not None:
            st.vwap, st.vwap_source = indicator_vwap, "INDICATORS.vwap"
        else:
            day_bars = [b for b in all_done if b.ts >= session_open]
            complete_day = (day_bars and day_bars[0].ts <= session_open
                            and len(segments(day_bars, self.c["max_gap_minutes"])) == 1)
            v = vwap_from_bars(day_bars) if complete_day else None
            if v is not None:
                st.vwap, st.vwap_source = v, "COMPUTED_FROM_FEED_1m"
        if st.vwap is not None:
            st.vwap_distance = price - st.vwap

        if len(done) < self.c["min_bars"]:
            st.reason = f"warming up: {len(done)}/{self.c['min_bars']} contiguous completed 1m bars"
            if len(done) < len(all_done):
                st.notes.append(f"data gap before {done[0].ts:%H:%M}" if done else "data gap")
            return st

        recent = done[-self.c["avg_range_bars"]:]
        floor = price * self.c["min_avg_range_pct"] / 100
        st.avg_range = max(mean(b.range for b in recent), floor)
        tol = st.avg_range * 0.25

        n = self.c["swing_lookaround"]
        gap = self.c["max_gap_minutes"]
        swings = find_swings_segmented(all_done, n, "1m", gap)
        if bars_5m:
            swings += find_swings_segmented([b for b in bars_5m if b.complete], n, "5m", gap * 5)
        st.swings = sorted(swings, key=lambda s: s.ts)
        st.swing_highs = [s for s in st.swings if s.kind == "H" and s.timeframe == "1m"]
        st.swing_lows = [s for s in st.swings if s.kind == "L" and s.timeframe == "1m"]
        st.high_seq = _seq(st.swing_highs, tol, "HH", "LH", "EH")
        st.low_seq = _seq(st.swing_lows, tol, "HL", "LL", "EL")
        if st.high_seq == "HH" and st.low_seq == "HL":
            st.trend = "UP"
        elif st.high_seq == "LH" and st.low_seq == "LL":
            st.trend = "DOWN"
        elif st.high_seq and st.low_seq:
            st.trend = "RANGE"

        k = self.c["momentum_lookback_bars"]
        ref_close = done[-k - 1].close if len(done) > k else done[0].open
        st.momentum = (price - ref_close) / st.avg_range
        m = st.momentum
        st.momentum_state = ("STRONG_UP" if m >= 3 else "UP" if m >= 1 else
                             "STRONG_DOWN" if m <= -3 else "DOWN" if m <= -1 else "FLAT")
        last3 = done[-3:]
        st.expansion = mean(b.range for b in last3) >= self.c["expansion_ratio"] * st.avg_range

        win = done[-self.c["consolidation_bars"]:]
        hi, lo = max(b.high for b in win), min(b.low for b in win)
        if hi - lo <= self.c["consolidation_max_ranges"] * st.avg_range:
            st.consolidation = True
            st.range_high, st.range_low = hi, lo
            if st.trend == "UNKNOWN":
                st.trend = "RANGE"

        if any(b.source.startswith("INTERNAL") for b in recent):
            st.notes.append("bar ranges from sampled observations (internally aggregated)")
        st.ready = True
        return st

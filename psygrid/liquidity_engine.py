"""Liquidity pools (equal highs / equal lows) and liquidity sweeps.

A sweep is recorded only when ALL of these hold (mirrored for the long side):

1. a reference level existed BEFORE the sweep bar (zone edge, prior swing,
   opening range, previous-day level)
2. the prior bar closed on the original side of the level
3. the sweep bar traded through it by a minimum penetration
4. price closed back on the original side within ``reclaim_bars``
5. the current price is still on the original side (reclaim holds)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .config import Config
from .models import Candle
from .structure_engine import StructureState, Swing, contiguous_tail


@dataclass
class Pool:
    price: float
    kind: str                # EQUAL_HIGHS | EQUAL_LOWS
    touches: int
    last_ts: datetime


@dataclass
class SweepEvent:
    direction: str           # BULLISH (lows swept, reclaimed) | BEARISH (highs swept, rejected)
    ref_price: float
    ref_label: str
    ref_zone_id: Optional[str]
    extreme: float           # furthest price reached through the level
    sweep_ts: datetime
    confirm_ts: datetime
    age_bars: int


@dataclass
class LiquidityState:
    pools: list[Pool] = field(default_factory=list)
    sweeps: list[SweepEvent] = field(default_factory=list)


def find_pools(swings: list[Swing], tol: float) -> list[Pool]:
    pools: list[Pool] = []
    for kind, label in (("H", "EQUAL_HIGHS"), ("L", "EQUAL_LOWS")):
        pts = sorted((s for s in swings if s.kind == kind), key=lambda s: s.price)
        group: list[Swing] = []
        for s in pts + [None]:
            if s is not None and (not group or s.price - group[0].price <= tol):
                group.append(s)
                continue
            if len(group) >= 2:
                price = max(g.price for g in group) if kind == "H" else min(g.price for g in group)
                pools.append(Pool(price, label, len(group), max(g.ts for g in group)))
            group = [s] if s is not None else []
    return pools


class LiquidityEngine:
    def __init__(self, cfg: Config):
        self.c = cfg["liquidity"]

    def references(self, st: StructureState, zones: list, or_end: datetime) -> list[tuple]:
        """(price_high_side, price_low_side, label, zone_id, formed_ts)"""
        refs = []
        for z in zones:
            if z.tier <= 2:
                # a zone is only a valid reference for bars after the engine knew about it
                refs.append((z.high, z.low, f"{z.id} {z.center:.0f}", z.id, z.first_seen))
        for s in st.swings:
            if s.timeframe == "1m":
                refs.append((s.price, s.price, f"swing {'high' if s.kind == 'H' else 'low'} {s.price:.0f}",
                             None, s.ts + timedelta(minutes=1)))
        if st.or_complete and st.or_high is not None:
            refs.append((st.or_high, st.or_high, f"OR high {st.or_high:.0f}", None, or_end))
            refs.append((st.or_low, st.or_low, f"OR low {st.or_low:.0f}", None, or_end))
        return refs

    def analyze(self, bars: list[Candle], st: StructureState, zones: list, price: float,
                or_end: datetime) -> LiquidityState:
        out = LiquidityState()
        if not st.ready or st.avg_range is None:
            return out
        tol = st.avg_range * self.c["equal_level_ranges"]
        out.pools = find_pools([s for s in st.swings if s.timeframe == "1m"], tol)
        done = contiguous_tail([b for b in bars if b.complete])
        pen = st.avg_range * self.c["min_penetration_ranges"]
        look = self.c["sweep_lookback_bars"]
        rb = self.c["reclaim_bars"]
        refs = self.references(st, zones, or_end)
        best: dict[str, SweepEvent] = {}
        start = max(1, len(done) - look)
        for i in range(start, len(done)):
            bar, prev = done[i], done[i - 1]
            window = done[max(0, i - 5):i + 1]
            new_high = bar.high >= max(b.high for b in window)
            new_low = bar.low <= min(b.low for b in window)
            for hi_px, lo_px, label, zid, formed in refs:
                if formed is not None and formed > bar.ts:
                    continue
                # BEARISH: sweep above the level, back below
                if new_high and prev.close < hi_px and bar.high > hi_px + pen and price < hi_px:
                    conf = next((done[j] for j in range(i, min(i + rb + 1, len(done)))
                                 if done[j].close < hi_px), None)
                    if conf is not None:
                        ext = max(b.high for b in done[i:done.index(conf) + 1])
                        ev = SweepEvent("BEARISH", hi_px, label, zid, ext, bar.ts,
                                        conf.ts + timedelta(minutes=1), len(done) - 1 - i)
                        self._keep(best, ev)
                # BULLISH: sweep below the level, back above
                if new_low and prev.close > lo_px and bar.low < lo_px - pen and price > lo_px:
                    conf = next((done[j] for j in range(i, min(i + rb + 1, len(done)))
                                 if done[j].close > lo_px), None)
                    if conf is not None:
                        ext = min(b.low for b in done[i:done.index(conf) + 1])
                        ev = SweepEvent("BULLISH", lo_px, label, zid, ext, bar.ts,
                                        conf.ts + timedelta(minutes=1), len(done) - 1 - i)
                        self._keep(best, ev)
        out.sweeps = [e for e in best.values() if e.age_bars <= self.c["max_sweep_age_bars"]]
        return out

    @staticmethod
    def _keep(best: dict, ev: SweepEvent) -> None:
        cur = best.get(ev.direction)
        # prefer the most recent; on ties prefer a zone-backed reference
        if cur is None or ev.confirm_ts > cur.confirm_ts or (
                ev.confirm_ts == cur.confirm_ts and ev.ref_zone_id and not cur.ref_zone_id):
            best[ev.direction] = ev

"""Underlying price history.

Two verified sources feed the bar series:

* FEED candles from the spot endpoint (``1m``/``5m``/``15m``/``1h`` arrays,
  source DHAN_WEBSOCKET_FULL / DHAN_HISTORICAL_API) — used as-is.
* Raw price OBSERVATIONS captured every poll from the gate-selected underlying
  source (spot ltp, or option-chain ``underlying_ltp`` + ``updated_at`` when the
  spot feed is not live). These are aggregated into 1-minute bars labelled
  ``INTERNAL_AGG_1m``. Internal bars carry no volume (the source has none) and
  their high/low only reflect the sampled observations, which is stated in the
  output. Higher timeframes are aggregated only when enough 1m bars exist.

Observations are persisted per day so a restart keeps the session history.
"""

from __future__ import annotations

import dataclasses
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .market_clock import IST
from .models import Candle, SpotData
from .schema_adapter import parse_ts


@dataclass
class Observation:
    ts: datetime
    price: float
    source: str


TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}


def with_completeness(c: Candle, tf: str, now: datetime) -> Candle:
    """A feed candle is complete only once its interval has ended."""
    done = c.ts + timedelta(minutes=TF_MINUTES.get(tf, 1)) <= now
    return c if done == c.complete else dataclasses.replace(c, complete=done)


def minute_floor(ts: datetime) -> datetime:
    return ts.replace(second=0, microsecond=0)


def aggregate(bars_1m: list[Candle], minutes: int, min_fill: float, label: str,
              now: Optional[datetime] = None) -> list[Candle]:
    """Aggregate 1m bars into N-minute bars anchored at 09:15 IST.

    A finished bucket is emitted only when at least ``min_fill`` of its
    constituent minutes exist (no bars are invented to fill gaps). The bucket
    still in progress at ``now`` is emitted with ``complete=False``.
    """
    buckets: dict[datetime, list[Candle]] = {}
    for b in bars_1m:
        anchor = b.ts.replace(hour=9, minute=15, second=0, microsecond=0)
        k = int((b.ts - anchor).total_seconds() // (minutes * 60))
        buckets.setdefault(anchor + timedelta(minutes=k * minutes), []).append(b)
    need = max(1, math.ceil(minutes * min_fill))
    out = []
    for start in sorted(buckets):
        grp = sorted(buckets[start], key=lambda c: c.ts)
        in_progress = now is not None and start + timedelta(minutes=minutes) > now
        if not in_progress and len(grp) < need:
            continue
        vols = [c.volume for c in grp]
        out.append(Candle(
            ts=start, open=grp[0].open, high=max(c.high for c in grp), low=min(c.low for c in grp),
            close=grp[-1].close, volume=sum(vols) if all(v is not None for v in vols) else None,
            source=label, complete=(not in_progress) and all(c.complete for c in grp),
            observations=sum(c.observations for c in grp),
        ))
    return out


class UnderlyingTracker:
    def __init__(self, index: str, store_dir: Optional[Path] = None, max_jump_pct: float = 2.0):
        self.index = index
        self.obs: list[Observation] = []
        self.feed_candles: dict[str, dict[datetime, Candle]] = {}
        self.store_dir = store_dir
        self.max_jump_pct = max_jump_pct
        self.rejected: list[str] = []
        self._loaded_date: Optional[str] = None

    # -------------------------------------------------------- persistence
    def _store_path(self, day: str) -> Optional[Path]:
        if self.store_dir is None:
            return None
        return self.store_dir / day / f"{self.index}_observations.jsonl"

    def load_day(self, day: str) -> int:
        """Reload today's persisted observations (only the same trading date)."""
        self._loaded_date = day
        path = self._store_path(day)
        if path is None or not path.exists():
            return 0
        n = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                ts = parse_ts(row["ts"])
                price = float(row["price"])
            except (ValueError, KeyError, TypeError):
                continue
            if ts is None or ts.strftime("%Y-%m-%d") != day or price <= 0:
                continue
            if self.obs and ts <= self.obs[-1].ts:
                continue
            self.obs.append(Observation(ts, price, str(row.get("source", "?"))))
            n += 1
        return n

    def _persist(self, o: Observation) -> None:
        path = self._store_path(o.ts.strftime("%Y-%m-%d"))
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": o.ts.isoformat(), "price": o.price, "source": o.source}) + "\n")

    # ------------------------------------------------------------- inputs
    def add_observation(self, ts: datetime, price: float, source: str) -> bool:
        """Add a verified observation. Duplicates / out-of-order / jumps are rejected."""
        ts = ts.astimezone(IST)
        if price is None or price <= 0:
            return False
        if self.obs:
            last = self.obs[-1]
            if ts <= last.ts:
                return False          # duplicate or older timestamp: no new information
            if ts.date() != last.ts.date():
                self.obs.clear()      # new session
            else:
                jump = abs(price - last.price) / last.price * 100
                if jump > self.max_jump_pct and (ts - last.ts).total_seconds() <= 120:
                    self.rejected.append(f"{ts:%H:%M:%S} jump {last.price}->{price} rejected")
                    return False
        o = Observation(ts, price, source)
        self.obs.append(o)
        self._persist(o)
        return True

    def update_feed_candles(self, spot: Optional[SpotData]) -> None:
        if spot is None:
            return
        for tf, rows in spot.candles.items():
            store = self.feed_candles.setdefault(tf, {})
            for c in rows:
                store[c.ts] = c

    # ------------------------------------------------------------ outputs
    @property
    def last(self) -> Optional[Observation]:
        return self.obs[-1] if self.obs else None

    def session_day(self, now: datetime) -> str:
        return now.astimezone(IST).strftime("%Y-%m-%d")

    def bars_1m(self, now: datetime) -> list[Candle]:
        """Merged 1m bars for today's session: FEED bars where they exist,
        INTERNAL_AGG bars from observations elsewhere. The current minute is
        returned as an incomplete bar."""
        day = now.astimezone(IST).date()
        merged: dict[datetime, Candle] = {
            ts: with_completeness(c, "1m", now) for ts, c in self.feed_candles.get("1m", {}).items()
            if ts.date() == day
        }
        by_min: dict[datetime, list[Observation]] = {}
        for o in self.obs:
            if o.ts.date() == day:
                by_min.setdefault(minute_floor(o.ts), []).append(o)
        cur_min = minute_floor(now.astimezone(IST))
        for m, grp in by_min.items():
            if m in merged:
                continue
            prices = [g.price for g in grp]
            merged[m] = Candle(ts=m, open=prices[0], high=max(prices), low=min(prices),
                               close=prices[-1], volume=None, source="INTERNAL_AGG_1m",
                               complete=m < cur_min, observations=len(prices))
        return [merged[k] for k in sorted(merged)]

    def completed_1m(self, now: datetime) -> list[Candle]:
        return [b for b in self.bars_1m(now) if b.complete]

    def bars(self, tf: str, now: datetime, min_fill: float) -> list[Candle]:
        """FEED bars for a timeframe when the feed has today's data, otherwise
        internal aggregation of the merged 1m series."""
        day = now.astimezone(IST).date()
        feed = [with_completeness(c, tf, now) for ts, c in sorted(self.feed_candles.get(tf, {}).items())
                if ts.date() == day]
        if feed:
            return feed
        minutes = {"5m": 5, "15m": 15, "1h": 60}[tf]
        return aggregate(self.completed_1m(now), minutes, min_fill, f"INTERNAL_AGG_{tf}", now)

    def previous_day_bars(self, now: datetime) -> list[Candle]:
        """Feed candles (any timeframe) from the most recent earlier date."""
        day = now.astimezone(IST).date()
        earlier: dict = {}
        for tf in ("1h", "15m", "5m", "1m"):
            for ts, c in self.feed_candles.get(tf, {}).items():
                if ts.date() < day:
                    earlier.setdefault(ts.date(), {}).setdefault(tf, []).append(c)
        if not earlier:
            return []
        last_day = max(earlier)
        tfs = earlier[last_day]
        for tf in ("1m", "5m", "15m", "1h"):          # finest timeframe available
            if tf in tfs:
                return sorted(tfs[tf], key=lambda c: c.ts)
        return []

    def coverage(self, now: datetime, session_open: datetime) -> dict:
        bars = self.bars_1m(now)
        if not bars:
            return {"bars": 0, "first": None, "gaps": 0, "from_open": False}
        expected = int((minute_floor(now) - session_open).total_seconds() // 60) + 1
        return {
            "bars": len(bars),
            "first": bars[0].ts,
            "gaps": max(0, expected - len(bars)),
            "from_open": bars[0].ts <= session_open,
            "internal": sum(1 for b in bars if b.source.startswith("INTERNAL")),
            "feed": sum(1 for b in bars if b.source.startswith("FEED")),
        }

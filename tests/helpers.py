"""Shared test helpers: real-schema fixtures re-timed to a chosen 'now'."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta

from psygrid.config import load_config
from psygrid.data_integrity import IntegrityGate
from psygrid.market_clock import IST
from psygrid.models import Candle, IndexSnapshot, RawResponse
from psygrid.schema_adapter import ADAPTERS

from sim import fixture

NOW = datetime(2026, 9, 24, 10, 35, 10, tzinfo=IST)


def retimed(now: datetime = NOW) -> dict[str, dict]:
    """Real NIFTY payloads with their timestamps moved to be fresh at ``now``."""
    opt = fixture("nifty-options")
    opt["updated_at"] = (now - timedelta(seconds=2)).isoformat()
    dep = fixture("nifty-depth")
    dep["updated_at"] = (now - timedelta(seconds=1)).isoformat()
    for c in dep["contracts"]:
        c["updated_at"] = c["quote_updated_at"] = (now - timedelta(seconds=1)).isoformat()
    return {"spot": fixture("nifty"), "options": opt, "depth": dep,
            "futures": fixture("nifty-futures"), "indicators": fixture("nifty-indicators")}


def raw(feed: str, payload, http: int | None = 200, now: datetime = NOW, error=None) -> RawResponse:
    body = json.dumps(payload).encode() if payload is not None else None
    return RawResponse(index="NIFTY", feed=feed, url=f"test://{feed}", fetched_at=now, http_status=http,
                       elapsed_ms=1.0, body=body, payload=payload, error=error)


def evaluate(payloads: dict, now: datetime = NOW, http: dict | None = None, prev=None):
    cfg = load_config()
    gate = IntegrityGate(cfg)
    raws, snap = {}, IndexSnapshot("NIFTY", now, None, None, None, None, None)
    attrs = {"spot": "spot", "options": "chain", "depth": "depth", "futures": "futures", "indicators": "indicators"}
    for feed, pl in payloads.items():
        code = (http or {}).get(feed, 503 if isinstance(pl, dict) and pl.get("status") in ("ERROR", "STARTING") else 200)
        raws[feed] = raw(feed, pl, code, now)
        if pl is not None:
            model, issues = ADAPTERS[feed](pl, "NIFTY")
            setattr(snap, attrs[feed], model)
            snap.adapter_issues[feed] = issues
    return gate.evaluate(snap, raws, *(prev or (None, None)))


def bars(prices: list[tuple[float, float, float, float]], start: datetime | None = None,
         source: str = "TEST_1m", volume: float | None = None) -> list[Candle]:
    start = start or datetime(2026, 9, 24, 10, 0, tzinfo=IST)
    return [Candle(start + timedelta(minutes=i), o, h, l, c, volume, source)
            for i, (o, h, l, c) in enumerate(prices)]


def line_bars(closes: list[float], spread: float = 2.0, **kw) -> list[Candle]:
    out, prev = [], closes[0]
    for c in closes:
        o = prev
        out.append((o, max(o, c) + spread, min(o, c) - spread, c))
        prev = c
    return bars(out, **kw)


def deep(d):
    return copy.deepcopy(d)

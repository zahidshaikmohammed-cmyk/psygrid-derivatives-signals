"""HTTP client for the PSYGRID public JSON endpoints (read-only).

Never raises on network or parse problems; every failure is returned inside a
``RawResponse`` so the integrity gate can decide what to do. Non-2xx statuses
are NOT treated as failures here: the live server returns HTTP 503 together
with a meaningful JSON payload (e.g. status=ERROR / STARTING), and the payload
is what the integrity gate evaluates.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Callable, Optional

import requests

from .config import Config, INDICES
from .market_clock import IST, now_ist
from .models import RawResponse

FEEDS = ("spot", "options", "depth", "indicators", "futures")


def endpoint_url(cfg: Config, index: str, feed: str) -> str:
    ep = cfg["endpoints"]
    return f"{ep['base_url']}{ep['prefix'][index]}{ep['feeds'][feed]}.json"


def decode_payload(body: Optional[bytes]) -> tuple[Optional[dict], Optional[str]]:
    if body is None:
        return None, "empty body"
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"malformed JSON: {type(exc).__name__}: {exc}"
    if not isinstance(data, dict):
        return None, f"unexpected top-level JSON type {type(data).__name__} (expected object)"
    return data, None


def _server_date(headers) -> Optional[datetime]:
    value = headers.get("Date") if headers is not None else None
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(IST)
    except (TypeError, ValueError):
        return None


class DataClient:
    def __init__(self, cfg: Config, getter: Optional[Callable] = None):
        self.cfg = cfg
        self.session = requests.Session()
        self._get = getter or self.session.get

    def fetch(self, index: str, feed: str) -> RawResponse:
        url = endpoint_url(self.cfg, index, feed)
        timeout = self.cfg["endpoints"]["timeout_seconds"]
        retries = int(self.cfg["endpoints"]["retries"])
        last_err = None
        for attempt in range(retries + 1):
            fetched_at = now_ist()
            t0 = time.monotonic()
            try:
                resp = self._get(url, timeout=timeout)
            except requests.RequestException as exc:
                last_err = f"{type(exc).__name__}: {exc}"
                continue
            elapsed = round((time.monotonic() - t0) * 1000, 1)
            body = resp.content
            payload, perr = decode_payload(body)
            return RawResponse(index=index, feed=feed, url=url, fetched_at=fetched_at,
                               http_status=resp.status_code, elapsed_ms=elapsed, body=body,
                               payload=payload, error=perr,
                               server_date=_server_date(getattr(resp, "headers", None)))
        return RawResponse(index=index, feed=feed, url=url, fetched_at=now_ist(),
                           http_status=None, elapsed_ms=None, body=None, payload=None,
                           error=f"endpoint unavailable: {last_err}")

    def fetch_all(self, indices=INDICES) -> dict[str, dict[str, RawResponse]]:
        jobs = [(i, f) for i in indices for f in FEEDS]
        out: dict[str, dict[str, RawResponse]] = {i: {} for i in indices}
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            for (i, f), res in zip(jobs, pool.map(lambda j: self.fetch(*j), jobs)):
                out[i][f] = res
        return out

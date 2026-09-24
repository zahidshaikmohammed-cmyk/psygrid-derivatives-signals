"""DATA INTEGRITY GATE (mandatory).

Evaluates every feed on its *payload and freshness*, not on the HTTP status
alone: the live server answers HTTP 503 with a structured JSON body (for
example ``status: ERROR`` for unresolved futures, ``status: STARTING`` for a
warming indicator engine, or a depth feed whose websocket dropped while its
per-contract quotes are still fresh). HTTP status is recorded as a note.

Feed states
    OK        usable as designed
    DEGRADED  partially usable (reason explains which part)
    BLOCKED   must not be used

Trading authorization for an index is BLOCKED when the market is not open per
the payload, the option chain is unusable, no fresh underlying price exists,
or independent sources disagree about the underlying price. Missing futures,
depth or indicators do NOT block; they lower the data-quality score and remove
their confirmation from the confluence engine.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .config import Config
from .models import FeedCheck, IndexSnapshot, RawResponse


@dataclass
class GateResult:
    index: str
    authorization: str                      # AUTHORIZED | BLOCKED
    reasons: list[str]                      # blocking reasons
    notes: list[str]                        # non-blocking observations
    feeds: dict[str, FeedCheck]
    underlying_price: Optional[float] = None
    underlying_ts: Optional[datetime] = None
    underlying_source: Optional[str] = None
    market_open: bool = False
    data_quality: float = 0.0
    depth_mode: str = "UNAVAILABLE"         # FULL | QUOTE_ONLY | UNAVAILABLE

    @property
    def authorized(self) -> bool:
        return self.authorization == "AUTHORIZED"

    def usable(self, feed: str) -> bool:
        fc = self.feeds.get(feed)
        return bool(fc and fc.usable)


def _age(ref: datetime, ts: Optional[datetime]) -> Optional[float]:
    return None if ts is None else (ref - ts).total_seconds()


def _fmt_age(age: Optional[float]) -> str:
    if age is None:
        return "n/a"
    if abs(age) < 120:
        return f"{age:.0f}s"
    return f"{age / 60:.0f} min"


class IntegrityGate:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.ic = cfg["integrity"]
        self._last_ts: dict[tuple[str, str], datetime] = {}

    # ----------------------------------------------------------- helpers
    def _base(self, feed: str, raw: Optional[RawResponse], issues: list[str]) -> FeedCheck:
        fc = FeedCheck(feed=feed, state="OK", http_status=raw.http_status if raw else None)
        if raw is None:
            fc.state, fc.reasons = "BLOCKED", ["not fetched"]
        elif raw.payload is None:
            fc.state = "BLOCKED"
            if raw.http_status is None:
                fc.reasons.append(raw.error or "endpoint unavailable")
            else:
                fc.reasons.append(f"HTTP {raw.http_status}: {raw.error or 'no JSON payload'}")
        elif raw.http_status is not None and raw.http_status != 200:
            fc.reasons.append(f"HTTP {raw.http_status} (evaluated on JSON payload)")
        for i in issues:
            if "symbol mismatch" in i:
                fc.state = "BLOCKED"
            fc.reasons.append(i)
        return fc

    def _block(self, fc: FeedCheck, reason: str) -> None:
        fc.state = "BLOCKED"
        fc.reasons.append(reason)

    def _freshness(self, fc: FeedCheck, ref: datetime, ts: Optional[datetime], max_age: float,
                   what: str, index: str) -> None:
        age = _age(ref, ts)
        fc.age_seconds = age
        if ts is None:
            self._block(fc, f"{what} timestamp missing")
            return
        if age < -self.ic["max_clock_skew_seconds"]:
            self._block(fc, f"{what} timestamp {ts:%H:%M:%S} is in the future")
        elif age > max_age:
            self._block(fc, f"stale: {what} {ts:%H:%M:%S} is {_fmt_age(age)} old (max {max_age:.0f}s)")
        key = (index, fc.feed)
        if self._last_ts.get(key) == ts and fc.state != "BLOCKED":
            fc.reasons.append("no new update since last poll (duplicate timestamp)")
        self._last_ts[key] = ts

    def _status(self, fc: FeedCheck, feed: str, status: Optional[str], error: Optional[str]) -> None:
        accepted = self.ic["accepted_feed_status"][feed]
        if status not in accepted:
            msg = f"status={status}" + (f" ({error})" if error else "")
            if status is not None and status not in ("ERROR", "STARTING"):
                msg += " — unrecognized status"
            self._block(fc, msg)

    def _market(self, fc: FeedCheck, market_status: Optional[str], market_open: Optional[bool]) -> None:
        if market_status not in self.ic["accepted_market_status"] or market_open is not True:
            self._block(fc, f"market_status={market_status}, market_open={market_open}")

    # ------------------------------------------------------------- main
    def evaluate(self, snap: IndexSnapshot, raws: dict[str, RawResponse],
                 prev_price: Optional[float] = None, prev_ts: Optional[datetime] = None) -> GateResult:
        ref = snap.ref_time
        idx = snap.index
        mx = self.ic["max_age_seconds"]
        feeds: dict[str, FeedCheck] = {}
        notes: list[str] = []
        reasons: list[str] = []

        # ---------------- spot index feed
        fc = self._base("spot", raws.get("spot"), snap.adapter_issues.get("spot", []))
        sp = snap.spot
        if fc.state != "BLOCKED" and sp is None:
            self._block(fc, "spot payload could not be normalized")
        if fc.state != "BLOCKED" and sp is not None:
            if sp.session_status not in self.ic["accepted_session_status"]:
                self._block(fc, f"session.status={sp.session_status}")
            if sp.synthetic:
                self._block(fc, "synthetic_candles=true")
            if sp.feed_last_error:
                fc.reasons.append(f"feed.last_error={sp.feed_last_error}")
            if fc.state != "BLOCKED":
                if sp.ltp is not None:
                    self._freshness(fc, ref, sp.ltp_ts, mx["spot_ltp"], "ltp_timestamp", idx)
                else:
                    last = sp.candles.get("1m", [])
                    last_ts = last[-1].ts + timedelta(minutes=1) if last else None
                    age = _age(ref, last_ts)
                    fc.age_seconds = age
                    detail = (f"ltp=null, feed.status={sp.feed_status}, feed.messages="
                              f"{sp.feed_messages:g}" if sp.feed_messages is not None else "ltp=null")
                    if last_ts is not None and age is not None and age <= self.ic["spot_candle_max_age_seconds"]:
                        fc.state = "DEGRADED"
                        fc.reasons.append(f"{detail}; 1m candles fresh (last close {last_ts:%H:%M})")
                    else:
                        lc = f"last 1m candle closed {last_ts:%H:%M} ({_fmt_age(age)} ago)" if last_ts else "no 1m candles"
                        self._block(fc, f"not a live price source: {detail}; {lc}")
        feeds["spot"] = fc

        # ---------------- option chain
        fc = self._base("options", raws.get("options"), snap.adapter_issues.get("options", []))
        ch = snap.chain
        if fc.state != "BLOCKED" and ch is None:
            self._block(fc, "option chain could not be normalized")
        if fc.state != "BLOCKED" and ch is not None:
            self._status(fc, "options", ch.status, None)
            self._market(fc, ch.market_status, ch.market_open)
            if ch.synthetic:
                self._block(fc, "synthetic_data=true")
            self._freshness(fc, ref, ch.updated_at, mx["options"], "updated_at", idx)
            if ch.underlying_ltp is None:
                self._block(fc, "underlying_ltp missing/zero")
            else:
                near = [q for (k, _), q in ch.quotes.items()
                        if abs(k - ch.underlying_ltp) <= ch.underlying_ltp * 0.01 and q.quote_valid]
                if len(near) < 4:
                    self._block(fc, f"only {len(near)} valid quotes within 1% of underlying")
            if ch.analytics and (ch.analytics.crossed_markets_detected or 0) > 0:
                fc.reasons.append(f"server reports {ch.analytics.crossed_markets_detected:g} crossed markets")
        feeds["options"] = fc

        # ---------------- depth
        fc = self._base("depth", raws.get("depth"), snap.adapter_issues.get("depth", []))
        dp = snap.depth
        depth_mode = "UNAVAILABLE"
        if fc.state != "BLOCKED" and dp is None:
            self._block(fc, "depth payload could not be normalized")
        if fc.state != "BLOCKED" and dp is not None:
            has_book = any(c.bids and c.asks for c in dp.contracts)
            book_ok = dp.status in self.ic["accepted_feed_status"]["depth"] and has_book
            self._market(fc, dp.market_status, dp.market_open)
            if dp.synthetic:
                self._block(fc, "synthetic_data=true")
            if fc.state != "BLOCKED" and book_ok:
                self._freshness(fc, ref, dp.updated_at, mx["depth"], "updated_at", idx)
                if fc.state != "BLOCKED":
                    depth_mode = "FULL"
            if fc.state != "BLOCKED" and not book_ok:
                # book unusable: fall back to fresh quote-level buy/sell totals if present
                ages = [_age(ref, c.quote_updated_at) for c in dp.contracts
                        if c.quote_updated_at and c.buy_qty is not None and c.sell_qty is not None]
                med = statistics.median(ages) if ages else None
                why = f"status={dp.status}" + (f" ({dp.error})" if dp.error else "")
                if not has_book:
                    why += "; bid/ask ladders empty"
                if med is not None and med <= mx["depth_quote"] and len(ages) >= 4:
                    fc.state = "DEGRADED"
                    fc.age_seconds = med
                    fc.reasons.append(f"{why}; using quote-level buy/sell totals "
                                      f"(median quote age {_fmt_age(med)})")
                    depth_mode = "QUOTE_ONLY"
                else:
                    self._block(fc, f"{why}; no fresh quote-level data either")
            crossed = sum(1 for c in dp.contracts if c.crossed_book)
            if crossed:
                fc.reasons.append(f"{crossed} crossed books excluded")
        feeds["depth"] = fc

        # ---------------- futures
        fc = self._base("futures", raws.get("futures"), snap.adapter_issues.get("futures", []))
        fu = snap.futures
        if fc.state != "BLOCKED" and fu is None:
            self._block(fc, "futures payload could not be normalized")
        if fc.state != "BLOCKED" and fu is not None:
            self._status(fc, "futures", fu.status, fu.error)
            if fc.state != "BLOCKED":
                self._market(fc, fu.market_status, fu.market_open)
                if fu.synthetic:
                    self._block(fc, "synthetic_data=true")
                if fu.last_price is None:
                    self._block(fc, "last_price missing/zero")
                self._freshness(fc, ref, fu.updated_at, mx["futures"], "updated_at", idx)
                if fu.bid is not None and fu.ask is not None and fu.ask < fu.bid:
                    self._block(fc, f"crossed futures quote bid {fu.bid} > ask {fu.ask}")
        feeds["futures"] = fc

        # ---------------- indicators
        fc = self._base("indicators", raws.get("indicators"), snap.adapter_issues.get("indicators", []))
        ind = snap.indicators
        if fc.state != "BLOCKED" and ind is None:
            self._block(fc, "indicator payload could not be normalized")
        if fc.state != "BLOCKED" and ind is not None:
            self._status(fc, "indicators", ind.status, None)
            if fc.state != "BLOCKED":
                if ind.synthetic:
                    self._block(fc, "synthetic_candles=true")
                bar_close = ind.as_of + timedelta(minutes=1) if ind.as_of else None
                self._freshness(fc, ref, bar_close, self.ic["indicators_max_bar_age_seconds"],
                                "latest bar (as_of+1m)", idx)
                if fc.state == "BLOCKED" and ind.server_freshness == "FRESH":
                    fc.reasons.append("server freshness field says FRESH; overridden by as_of age")
                if fc.state != "BLOCKED" and not ind.values:
                    fc.state = "DEGRADED"
                    fc.reasons.append("no indicator is ready yet")
        feeds["indicators"] = fc

        # ---------------- underlying price selection + cross-checks
        u_price = u_ts = u_src = None
        if feeds["spot"].state == "OK" and sp is not None:
            u_price, u_ts, u_src = sp.ltp, sp.ltp_ts, "SPOT_FEED.ltp"
        elif feeds["options"].usable and ch is not None:
            u_price, u_ts, u_src = ch.underlying_ltp, ch.updated_at, "OPTION_CHAIN.underlying_ltp"
            notes.append("underlying price taken from option chain (spot feed not live)")
        elif depth_mode == "FULL" and dp is not None and dp.underlying_ltp:
            u_price, u_ts, u_src = dp.underlying_ltp, dp.updated_at, "DEPTH.underlying_ltp"

        checks = []
        if feeds["spot"].state == "OK" and sp:
            checks.append(("spot", sp.ltp))
        if feeds["options"].usable and ch:
            checks.append(("options", ch.underlying_ltp))
        if depth_mode == "FULL" and dp and dp.underlying_ltp:
            checks.append(("depth", dp.underlying_ltp))
        lim = self.ic["max_underlying_divergence_pct"]
        # indicator last_price is a completed-bar close (up to a few minutes old): it can
        # only disqualify the indicator feed, never block trading
        if feeds["indicators"].usable and ind and ind.last_price and checks:
            ref_px = checks[0][1]
            div = abs(ind.last_price - ref_px) / ref_px * 100
            if div > self.ic["max_indicator_divergence_pct"]:
                self._block(feeds["indicators"], f"last_price {ind.last_price:.2f} diverges {div:.2f}% "
                                                 f"from {checks[0][0]} {ref_px:.2f}")
        for i in range(len(checks)):
            for j in range(i + 1, len(checks)):
                a, b = checks[i], checks[j]
                div = abs(a[1] - b[1]) / b[1] * 100
                if div > lim:
                    reasons.append(f"inconsistent underlying: {a[0]}={a[1]:.2f} vs {b[0]}={b[1]:.2f} "
                                   f"({div:.2f}% > {lim}%)")

        if feeds["futures"].usable and fu and fu.last_price and u_price:
            basis_pct = abs(fu.last_price - u_price) / u_price * 100
            if basis_pct > self.ic["max_futures_basis_pct"]:
                self._block(feeds["futures"], f"basis {basis_pct:.2f}% implausible vs underlying")

        if u_price is not None and prev_price is not None and prev_ts is not None and u_ts is not None:
            jump = abs(u_price - prev_price) / prev_price * 100
            if jump > self.ic["max_tick_jump_pct"] and (u_ts - prev_ts).total_seconds() <= 120:
                reasons.append(f"impossible price jump {prev_price:.2f} -> {u_price:.2f} ({jump:.2f}%)")

        # ---------------- authorization
        market_open = feeds["options"].usable
        if not feeds["options"].usable:
            reasons.insert(0, "option chain unusable: " + "; ".join(feeds["options"].reasons))
        if u_price is None:
            reasons.append("no fresh underlying price from any source")

        dq = 1.0
        if feeds["spot"].state != "OK":
            dq -= 0.10
        if not feeds["futures"].usable:
            dq -= 0.25
        if depth_mode == "UNAVAILABLE":
            dq -= 0.25
        elif depth_mode == "QUOTE_ONLY":
            dq -= 0.12
        if not feeds["indicators"].usable or feeds["indicators"].state == "DEGRADED":
            dq -= 0.15
        if reasons:
            dq = 0.0

        return GateResult(index=idx, authorization="BLOCKED" if reasons else "AUTHORIZED",
                          reasons=reasons, notes=notes, feeds=feeds, underlying_price=u_price,
                          underlying_ts=u_ts, underlying_source=u_src, market_open=market_open,
                          data_quality=max(0.0, round(dq, 2)), depth_mode=depth_mode)

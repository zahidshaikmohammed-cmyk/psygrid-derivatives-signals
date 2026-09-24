"""Raw JSON -> normalized models, using ONLY field names observed in the live
samples (samples/schema/20260924_103510/schema_report.md, schema_version 3.0).

Rules
-----
* A missing key, a wrong type or a non-finite number becomes ``None``.
* On the option chain, 0 is the server's placeholder for "no data" (observed on
  every untraded strike: last_price, bid, ask, IV and greeks are all 0 together),
  so prices/IV/greeks that are <= 0 become ``None``. OI and volume keep 0
  because zero OI / zero volume are real values.
* Futures fields were only ever observed as ``null`` (status=ERROR). They are
  parsed defensively by name; any value that does not have the expected type
  is dropped, not coerced.
* Every adapter returns ``(model | None, issues)``; issues are human-readable
  and feed the data-integrity gate.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Optional

from .market_clock import IST
from .models import (
    Candle, ChainAnalytics, DepthContract, DepthData, DepthLevel, FuturesData,
    IndicatorData, OptionChain, OptionQuote, SpotData,
)

SPOT_TS_FORMAT = "%Y-%m-%d %H:%M:%S IST"      # observed: "2026-09-24 09:15:00 IST"


# ----------------------------------------------------------------- primitives

def num(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    f = float(value)
    return f if math.isfinite(f) else None


def pos(value: Any) -> Optional[float]:
    f = num(value)
    return f if f is not None and f > 0 else None


def nonneg(value: Any) -> Optional[float]:
    f = num(value)
    return f if f is not None and f >= 0 else None


def string(value: Any) -> Optional[str]:
    return value if isinstance(value, str) else None


def boolean(value: Any) -> Optional[bool]:
    return value if isinstance(value, bool) else None


def parse_ts(value: Any) -> Optional[datetime]:
    """Parse the two timestamp formats observed in the feeds.

    * "YYYY-MM-DD HH:MM:SS IST"  (spot candles, session.current_time_ist)
    * ISO-8601 with offset       (updated_at, as_of, quote_updated_at)
    Naive ISO strings (no offset) were never observed and are rejected.
    """
    if not isinstance(value, str) or not value:
        return None
    if value.endswith(" IST"):
        try:
            return datetime.strptime(value, SPOT_TS_FORMAT).replace(tzinfo=IST)
        except ValueError:
            return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(IST)


def parse_epoch(value: Any) -> Optional[float]:
    return pos(value)


# ------------------------------------------------------------------------ spot

def adapt_candle(raw: Any, source: str) -> tuple[Optional[Candle], Optional[str]]:
    if not isinstance(raw, dict):
        return None, f"{source}: candle is not an object"
    ts = parse_ts(raw.get("timestamp"))
    o, h, l, c = (pos(raw.get(k)) for k in ("open", "high", "low", "close"))
    if ts is None or None in (o, h, l, c):
        return None, f"{source}: candle missing/invalid timestamp or OHLC"
    if not (l <= min(o, c) and h >= max(o, c) and h >= l):
        return None, f"{source}: impossible OHLC at {raw.get('timestamp')}"
    return Candle(ts=ts, open=o, high=h, low=l, close=c, volume=nonneg(raw.get("volume")),
                  source=source), None


def adapt_spot(p: dict, expected_symbol: str) -> tuple[Optional[SpotData], list[str]]:
    issues: list[str] = []
    if not isinstance(p, dict):
        return None, ["spot payload is not an object"]
    symbol = string(p.get("symbol"))
    if symbol != expected_symbol:
        issues.append(f"symbol mismatch: expected {expected_symbol}, got {symbol!r}")
        return None, issues
    session = p.get("session") if isinstance(p.get("session"), dict) else {}
    feed = p.get("feed") if isinstance(p.get("feed"), dict) else {}
    if not session:
        issues.append("spot.session missing")
    if not feed:
        issues.append("spot.feed missing")

    candles: dict[str, list[Candle]] = {}
    timeframes = p.get("timeframes") if isinstance(p.get("timeframes"), list) else []
    for tf in timeframes:
        if not isinstance(tf, str):
            continue
        rows = p.get(tf)
        if not isinstance(rows, list):
            issues.append(f"spot.{tf} missing or not a list")
            continue
        parsed: list[Candle] = []
        seen = set()
        for row in rows:
            c, err = adapt_candle(row, f"FEED_{tf}")
            if err:
                issues.append(err)
                continue
            if c.ts in seen:
                issues.append(f"duplicate candle timestamp {c.ts:%H:%M} in {tf}")
                continue
            seen.add(c.ts)
            parsed.append(c)
        candles[tf] = sorted(parsed, key=lambda x: x.ts)

    cs = p.get("candle_source") if isinstance(p.get("candle_source"), dict) else {}
    return SpotData(
        symbol=symbol,
        session_status=string(session.get("status")),
        session_date=string(session.get("date")),
        server_time=parse_ts(session.get("current_time_ist")),
        feed_status=string(feed.get("status")),
        feed_messages=num(feed.get("messages")),
        feed_last_error=string(feed.get("last_error")) or None,
        last_tick_epoch=parse_epoch(feed.get("last_tick_received_epoch")),
        ltp=pos(p.get("ltp")),
        ltp_ts=parse_ts(p.get("ltp_timestamp")),
        candles=candles,
        candle_source={k: v for k, v in cs.items() if isinstance(v, str)},
        synthetic=boolean(p.get("synthetic_candles")),
    ), issues


# ------------------------------------------------------------------- options

def _adapt_quote(strike: float, otype: str, raw: Any) -> Optional[OptionQuote]:
    if not isinstance(raw, dict):
        return None
    g = raw.get("greeks") if isinstance(raw.get("greeks"), dict) else {}
    delta = num(g.get("delta"))
    gamma = pos(g.get("gamma"))
    theta = num(g.get("theta"))
    vega = pos(g.get("vega"))
    # all-zero greeks are the server placeholder for "not computed"
    if delta == 0:
        delta = None
    if theta == 0:
        theta = None
    sid = raw.get("security_id")
    return OptionQuote(
        strike=strike, option_type=otype,
        security_id=int(sid) if isinstance(sid, int) and not isinstance(sid, bool) else None,
        ltp=pos(raw.get("last_price")),
        bid=pos(raw.get("top_bid_price")),
        ask=pos(raw.get("top_ask_price")),
        bid_qty=nonneg(raw.get("top_bid_quantity")),
        ask_qty=nonneg(raw.get("top_ask_quantity")),
        volume=nonneg(raw.get("volume")),
        oi=nonneg(raw.get("oi")),
        prev_oi=nonneg(raw.get("previous_oi")),
        prev_close=pos(raw.get("previous_close_price")),
        prev_volume=nonneg(raw.get("previous_volume")),
        avg_price=pos(raw.get("average_price")),
        iv=pos(raw.get("implied_volatility")),
        delta=delta, gamma=gamma, theta=theta, vega=vega,
    )


def _adapt_analytics(a: Any) -> Optional[ChainAnalytics]:
    if not isinstance(a, dict):
        return None
    cls: dict[tuple[float, str], str] = {}
    for c in a.get("contracts") or []:
        if not isinstance(c, dict):
            continue
        k = num(c.get("strike"))
        t = string(c.get("option_type"))
        v = string(c.get("oi_change_classification"))
        if k is not None and t in ("CE", "PE") and v:
            cls[(k, t)] = v
    dq = a.get("data_quality") if isinstance(a.get("data_quality"), dict) else {}

    def flist(v):
        return [f for f in (num(x) for x in v) if f is not None] if isinstance(v, list) else []

    return ChainAnalytics(
        pcr_oi=num(a.get("pcr_oi")), pcr_volume=num(a.get("pcr_volume")),
        atm_strike=pos(a.get("atm_strike")), max_pain_strike=pos(a.get("max_pain_strike")),
        resistance_strikes=flist(a.get("resistance_strikes")),
        support_strikes=flist(a.get("support_strikes")),
        total_call_oi=nonneg(a.get("total_call_oi")), total_put_oi=nonneg(a.get("total_put_oi")),
        total_call_volume=nonneg(a.get("total_call_volume")),
        total_put_volume=nonneg(a.get("total_put_volume")),
        avg_call_iv=pos(a.get("avg_call_iv")), avg_put_iv=pos(a.get("avg_put_iv")),
        iv_skew=num(a.get("iv_skew")), oi_change_class=cls,
        crossed_markets_detected=num(dq.get("crossed_markets_detected")),
        duplicate_security_ids=num(dq.get("duplicate_security_ids")),
    )


def adapt_options(p: dict, expected_symbol: str) -> tuple[Optional[OptionChain], list[str]]:
    issues: list[str] = []
    if not isinstance(p, dict):
        return None, ["options payload is not an object"]
    symbol = string(p.get("symbol"))
    if symbol != expected_symbol:
        return None, [f"symbol mismatch: expected {expected_symbol}, got {symbol!r}"]
    rows = p.get("strikes")
    quotes: dict[tuple[float, str], OptionQuote] = {}
    malformed = 0
    if not isinstance(rows, list):
        issues.append("options.strikes missing or not a list")
        rows = []
    for row in rows:
        strike = pos(row.get("strike")) if isinstance(row, dict) else None
        if strike is None:
            malformed += 1
            continue
        for otype, key in (("CE", "ce"), ("PE", "pe")):
            q = _adapt_quote(strike, otype, row.get(key))
            if q is None:
                malformed += 1
                continue
            if (strike, otype) in quotes:
                issues.append(f"duplicate option record {strike:g} {otype}")
                continue
            quotes[(strike, otype)] = q
    if malformed:
        issues.append(f"{malformed} malformed option records skipped")
    el = p.get("expiry_list")
    return OptionChain(
        symbol=symbol, status=string(p.get("status")),
        market_status=string(p.get("market_status")), market_open=boolean(p.get("market_open")),
        underlying_ltp=pos(p.get("underlying_ltp")), expiry=string(p.get("expiry")),
        expiry_list=[x for x in el if isinstance(x, str)] if isinstance(el, list) else [],
        updated_at=parse_ts(p.get("updated_at")), fetch_count=num(p.get("fetch_count")),
        synthetic=boolean(p.get("synthetic_data")), quotes=quotes,
        strikes=sorted({k for k, _ in quotes}), analytics=_adapt_analytics(p.get("analytics")),
        malformed_records=malformed,
    ), issues


# --------------------------------------------------------------------- depth

def _levels(raw: Any) -> tuple[list[DepthLevel], int]:
    out, bad = [], 0
    if not isinstance(raw, list):
        return out, 1
    for r in raw:
        if not isinstance(r, dict):
            bad += 1
            continue
        lvl, price, qty = num(r.get("level")), pos(r.get("price")), nonneg(r.get("quantity"))
        if lvl is None or price is None or qty is None:
            bad += 1
            continue
        out.append(DepthLevel(level=int(lvl), price=price, quantity=qty, orders=nonneg(r.get("orders"))))
    return sorted(out, key=lambda x: x.level), bad


def adapt_depth(p: dict, expected_symbol: str) -> tuple[Optional[DepthData], list[str]]:
    issues: list[str] = []
    if not isinstance(p, dict):
        return None, ["depth payload is not an object"]
    symbol = string(p.get("symbol"))
    if symbol != expected_symbol:
        return None, [f"symbol mismatch: expected {expected_symbol}, got {symbol!r}"]
    contracts: list[DepthContract] = []
    bad_levels = 0
    for c in p.get("contracts") or []:
        if not isinstance(c, dict):
            issues.append("depth contract is not an object")
            continue
        strike, otype = pos(c.get("strike")), string(c.get("option_type"))
        if strike is None or otype not in ("CE", "PE"):
            issues.append("depth contract missing strike/option_type")
            continue
        bids, b1 = _levels(c.get("bid"))
        asks, b2 = _levels(c.get("ask"))
        bad_levels += b1 + b2
        contracts.append(DepthContract(
            security_id=string(c.get("security_id")), strike=strike, option_type=otype,
            expiry=string(c.get("expiry")), bids=bids, asks=asks,
            ltp=pos(c.get("last_price")), avg_price=pos(c.get("average_price")),
            buy_qty=nonneg(c.get("buy_quantity")), sell_qty=nonneg(c.get("sell_quantity")),
            volume=nonneg(c.get("volume")), oi=nonneg(c.get("oi")),
            quote_updated_at=parse_ts(c.get("quote_updated_at")),
            updated_at=parse_ts(c.get("updated_at")),
            crossed_book=boolean(c.get("crossed_book")),
        ))
    if bad_levels:
        issues.append(f"{bad_levels} malformed depth levels skipped")
    return DepthData(
        symbol=symbol, status=string(p.get("status")), market_status=string(p.get("market_status")),
        market_open=boolean(p.get("market_open")), underlying_ltp=pos(p.get("underlying_ltp")),
        expiry=string(p.get("expiry")), depth_levels=int(num(p.get("depth_levels")) or 0) or None,
        contracts=contracts, updated_at=parse_ts(p.get("updated_at")),
        packet_count=num(p.get("packet_count")), synthetic=boolean(p.get("synthetic_data")),
        error=string(p.get("error")),
    ), issues


# ------------------------------------------------------------------- futures

def adapt_futures(p: dict, expected_symbol: str) -> tuple[Optional[FuturesData], list[str]]:
    if not isinstance(p, dict):
        return None, ["futures payload is not an object"]
    symbol = string(p.get("symbol"))
    if symbol != expected_symbol:
        return None, [f"symbol mismatch: expected {expected_symbol}, got {symbol!r}"]
    raw_ohlc = p.get("ohlc")
    ohlc = None
    if isinstance(raw_ohlc, dict):
        vals = {k: pos(raw_ohlc.get(k)) for k in ("open", "high", "low", "close")}
        ohlc = {k: v for k, v in vals.items() if v is not None} or None
    return FuturesData(
        symbol=symbol, status=string(p.get("status")), market_status=string(p.get("market_status")),
        market_open=boolean(p.get("market_open")), trading_symbol=string(p.get("trading_symbol")),
        expiry=string(p.get("expiry")), last_price=pos(p.get("last_price")), ohlc=ohlc,
        volume=nonneg(p.get("volume")), oi=nonneg(p.get("oi")), oi_change=num(p.get("oi_change")),
        average_price=pos(p.get("average_price")), buy_qty=nonneg(p.get("buy_quantity")),
        sell_qty=nonneg(p.get("sell_quantity")), bid=pos(p.get("top_bid_price")),
        ask=pos(p.get("top_ask_price")), updated_at=parse_ts(p.get("updated_at")),
        synthetic=boolean(p.get("synthetic_data")), error=string(p.get("error")),
    ), []


# ---------------------------------------------------------------- indicators

# Indicators whose value semantics are unambiguous from their names. Encodings
# never observed populated (e.g. supertrend_direction) are deliberately excluded.
USED_INDICATORS = ("vwap", "ema_9", "ema_20", "rsi_14", "macd_histogram", "adx_14",
                   "plus_di_14", "minus_di_14", "rvol_20", "atr_14")


def adapt_indicators(p: dict, expected_symbol: str) -> tuple[Optional[IndicatorData], list[str]]:
    issues: list[str] = []
    if not isinstance(p, dict):
        return None, ["indicators payload is not an object"]
    symbol = string(p.get("symbol"))
    if symbol != expected_symbol:
        return None, [f"symbol mismatch: expected {expected_symbol}, got {symbol!r}"]
    res = p.get("result") if isinstance(p.get("result"), dict) else None
    values: dict[str, float] = {}
    not_ready: list[str] = []
    as_of = bar_count = last_price = prev_close = today_open = fresh = synthetic = None
    if res is not None:
        ind = res.get("indicators") if isinstance(res.get("indicators"), dict) else {}
        status = res.get("indicator_status") if isinstance(res.get("indicator_status"), dict) else {}
        for name in USED_INDICATORS:
            st = status.get(name) if isinstance(status.get(name), dict) else {}
            v = num(ind.get(name))
            if st.get("ready") is True and v is not None:
                values[name] = v
            else:
                not_ready.append(name)
        as_of = parse_ts(res.get("as_of"))
        bar_count = num(res.get("bar_count"))
        last_price = pos(res.get("last_price"))
        prev_close = pos(res.get("previous_close"))
        today_open = pos(res.get("today_open"))
        fr = res.get("freshness") if isinstance(res.get("freshness"), dict) else {}
        fresh = string(fr.get("status"))
        synthetic = boolean(res.get("synthetic_candles"))
    elif p.get("status") == "OK":
        issues.append("indicators status OK but result missing")
    return IndicatorData(
        symbol=symbol, status=string(p.get("status")), timeframe=string(p.get("timeframe")),
        as_of=as_of, bar_count=bar_count, last_price=last_price, previous_close=prev_close,
        today_open=today_open, values=values, not_ready=not_ready, server_freshness=fresh,
        synthetic=synthetic,
    ), issues


ADAPTERS = {
    "spot": adapt_spot, "options": adapt_options, "depth": adapt_depth,
    "futures": adapt_futures, "indicators": adapt_indicators,
}

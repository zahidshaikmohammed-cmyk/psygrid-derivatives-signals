"""Adapter tests against trimmed REAL payloads (tests/fixtures)."""

from datetime import datetime

from psygrid.data_client import decode_payload
from psygrid.market_clock import IST
from psygrid.schema_adapter import (adapt_depth, adapt_futures, adapt_indicators, adapt_options, adapt_spot,
                                    parse_ts)

from helpers import deep
from sim import fixture


def test_parse_ts_observed_formats():
    assert parse_ts("2026-09-24 09:15:00 IST") == datetime(2026, 9, 24, 9, 15, tzinfo=IST)
    assert parse_ts("2026-09-24T10:34:58.610102+05:30").hour == 10
    assert parse_ts("2026-09-24T09:16:00+05:30").minute == 16
    assert parse_ts("2026-09-24T10:00:00") is None           # naive ISO never observed -> rejected
    assert parse_ts(None) is None and parse_ts(17) is None and parse_ts("garbage") is None


def test_spot_real_payload_ltp_null():
    s, issues = adapt_spot(fixture("nifty"), "NIFTY")
    assert s.ltp is None and s.ltp_ts is None
    assert s.session_status == "LIVE" and s.feed_status == "CONNECTED"
    assert s.candles["1m"] == [] and s.synthetic is False
    assert issues == []


def test_spot_candles_parsed_and_impossible_rejected():
    p = fixture("banknifty")
    s, _ = adapt_spot(p, "BANKNIFTY")
    assert len(s.candles["1m"]) == 2 and s.candles["1m"][0].open == 55710.6
    p["1m"].append({"timestamp": "2026-09-24 09:17:00 IST", "open": 10, "high": 5, "low": 20, "close": 10,
                    "volume": 1})
    p["1m"].append(dict(p["1m"][0]))                          # duplicate timestamp
    s, issues = adapt_spot(p, "BANKNIFTY")
    assert len(s.candles["1m"]) == 2
    assert any("impossible OHLC" in i for i in issues) and any("duplicate" in i for i in issues)


def test_symbol_mismatch():
    s, issues = adapt_spot(fixture("nifty"), "SENSEX")
    assert s is None and "symbol mismatch" in issues[0]


def test_options_zero_placeholders_become_none():
    ch, issues = adapt_options(fixture("nifty-options"), "NIFTY")
    assert ch.underlying_ltp == 23228.6 and ch.status == "LIVE" and ch.market_open is True
    q = ch.quote(23250.0, "CE")
    assert q.ltp == 109.5 and q.bid == 109.5 and q.ask == 109.7 and q.delta == 0.52066
    assert q.oi_change == 9398935 - 990925
    assert round(q.spread, 2) == 0.2 and q.spread_pct < 0.2
    far = [q for q in ch.quotes.values() if q.oi == 0]
    for q in far[:5]:
        assert q.ltp is None and q.iv is None and q.delta is None   # 0 == no data
    assert ch.analytics.atm_strike == 23250.0 and ch.analytics.oi_change_class


def test_options_missing_fields_and_malformed_records():
    p = fixture("nifty-options")
    del p["strikes"][0]["ce"]["last_price"]
    del p["strikes"][1]["pe"]["greeks"]
    p["strikes"][2]["ce"]["top_bid_price"] = "abc"
    p["strikes"].append({"strike": None})
    p["strikes"].append("not-a-dict")
    ch, issues = adapt_options(p, "NIFTY")
    k0, k1, k2 = (p["strikes"][i]["strike"] for i in range(3))
    assert ch.quote(k0, "CE").ltp is None
    assert ch.quote(k1, "PE").delta is None
    assert ch.quote(k2, "CE").bid is None
    assert any("malformed" in i for i in issues)


def test_depth_real_and_error_payload():
    d, _ = adapt_depth(fixture("nifty-depth"), "NIFTY")
    c = d.contracts[0]
    assert len(c.bids) == 20 and c.bids[0].level == 1 and c.asks[0].price > c.bids[0].price
    e, _ = adapt_depth(fixture("sensex-depth"), "SENSEX")
    assert e.status == "ERROR" and e.updated_at is None and "WebSocket" in e.error
    assert all(not x.bids and not x.asks for x in e.contracts)
    assert all(x.quote_updated_at is not None for x in e.contracts)


def test_futures_error_payload_all_none():
    f, _ = adapt_futures(fixture("nifty-futures"), "NIFTY")
    assert f.status == "ERROR" and "NOT_RESOLVED" in f.error
    assert f.last_price is None and f.ohlc is None and f.updated_at is None


def test_indicators_only_ready_values_used():
    i, _ = adapt_indicators(fixture("banknifty-indicators"), "BANKNIFTY")
    assert i.status == "OK" and set(i.values) == {"vwap"}          # ema/rsi not ready
    assert "rsi_14" in i.not_ready and i.as_of.minute == 16 and i.server_freshness == "FRESH"
    s, _ = adapt_indicators(fixture("nifty-indicators"), "NIFTY")
    assert s.status == "STARTING" and s.values == {} and s.as_of is None


def test_decode_payload_malformed_and_non_object():
    assert decode_payload(b"{bad")[0] is None and "malformed JSON" in decode_payload(b"{bad")[1]
    assert decode_payload(b"[1,2]")[0] is None
    assert decode_payload(None) == (None, "empty body")
    assert decode_payload(b'{"a": 1}') == ({"a": 1}, None)


def test_adapters_never_raise_on_garbage():
    for fn in (adapt_spot, adapt_options, adapt_depth, adapt_futures, adapt_indicators):
        for junk in ({}, {"symbol": "NIFTY"}, {"symbol": "NIFTY", "strikes": 5, "contracts": "x",
                                                "result": [], "session": 3, "1m": None, "timeframes": ["1m"]}):
            fn(deep(junk), "NIFTY")

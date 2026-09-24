"""Data-integrity gate: HTTP 503 handling by payload, staleness, errors."""

from datetime import timedelta

from helpers import NOW, evaluate, retimed
from sim import fixture


def test_live_real_payload_authorized_with_futures_and_indicators_blocked():
    g = evaluate(retimed())
    assert g.authorization == "AUTHORIZED"
    assert g.underlying_source == "OPTION_CHAIN.underlying_ltp" and g.underlying_price == 23228.6
    assert g.feeds["options"].state == "OK" and g.feeds["depth"].state == "OK"
    assert g.feeds["futures"].state == "BLOCKED"
    assert any("DHAN_NIFTY_FUTURES_NOT_RESOLVED" in r for r in g.feeds["futures"].reasons)
    assert any("HTTP 503" in r for r in g.feeds["futures"].reasons)
    assert g.feeds["indicators"].state == "BLOCKED" and any("STARTING" in r for r in g.feeds["indicators"].reasons)
    assert g.feeds["spot"].state == "BLOCKED"
    assert g.data_quality < 1.0


def test_http_503_with_live_fresh_payload_is_usable():
    g = evaluate(retimed(), http={"options": 503})
    assert g.feeds["options"].state == "OK" and g.authorized
    assert any("HTTP 503" in r for r in g.feeds["options"].reasons)


def test_stale_option_chain_blocks_trading():
    g = evaluate(retimed(), now=NOW + timedelta(minutes=5))
    assert g.authorization == "BLOCKED"
    assert any("stale" in r for r in g.feeds["options"].reasons)


def test_option_status_error_blocks():
    p = retimed()
    p["options"]["status"] = "ERROR"
    g = evaluate(p)
    assert not g.authorized and g.feeds["options"].state == "BLOCKED"


def test_invalid_market_status_blocks():
    p = retimed()
    p["options"]["market_status"] = "CLOSED"
    p["options"]["market_open"] = False
    g = evaluate(p)
    assert not g.authorized and any("market_status=CLOSED" in r for r in g.reasons)


def test_unrecognized_status_fails_closed():
    p = retimed()
    p["options"]["status"] = "WEIRD"
    g = evaluate(p)
    assert not g.authorized and any("unrecognized" in r for r in g.feeds["options"].reasons)


def test_endpoint_unavailable():
    p = retimed()
    p["options"] = None
    g = evaluate(p, http={"options": None})
    assert not g.authorized and g.feeds["options"].state == "BLOCKED"


def test_malformed_json_blocks():
    from psygrid.config import load_config
    from psygrid.data_integrity import IntegrityGate
    from psygrid.models import IndexSnapshot, RawResponse
    r = RawResponse("NIFTY", "options", "u", NOW, 200, 1.0, b"{oops", None, "malformed JSON: x")
    g = IntegrityGate(load_config()).evaluate(IndexSnapshot("NIFTY", NOW, None, None, None, None, None),
                                              {"options": r})
    assert not g.authorized
    assert any("malformed JSON" in x for x in g.feeds["options"].reasons)


def test_zero_underlying_blocks():
    p = retimed()
    p["options"]["underlying_ltp"] = 0
    g = evaluate(p)
    assert not g.authorized and any("underlying_ltp" in r for r in g.reasons)


def test_zero_prices_near_atm_block():
    p = retimed()
    for row in p["options"]["strikes"]:
        for side in ("ce", "pe"):
            row[side]["top_bid_price"] = 0
    g = evaluate(p)
    assert not g.authorized and any("valid quotes" in r for r in g.reasons)


def test_synthetic_data_blocks():
    p = retimed()
    p["options"]["synthetic_data"] = True
    assert not evaluate(p).authorized


def test_inconsistent_underlying_blocks():
    p = retimed()
    p["depth"]["underlying_ltp"] = p["options"]["underlying_ltp"] * 1.01
    g = evaluate(p)
    assert not g.authorized and any("inconsistent underlying" in r for r in g.reasons)


def test_impossible_jump_blocks():
    g = evaluate(retimed(), prev=(20000.0, NOW - timedelta(seconds=20)))
    assert not g.authorized and any("impossible price jump" in r for r in g.reasons)


def test_future_timestamp_blocks():
    p = retimed(NOW + timedelta(minutes=10))
    g = evaluate(p)
    assert not g.authorized and any("future" in r for r in g.feeds["options"].reasons)


def test_depth_error_with_fresh_quotes_is_degraded_quote_only():
    p = retimed()
    d = fixture("sensex-depth")
    d["symbol"] = "NIFTY"
    for c in d["contracts"]:
        c["quote_updated_at"] = (NOW - timedelta(seconds=3)).isoformat()
    d["underlying_ltp"] = p["options"]["underlying_ltp"]
    p["depth"] = d
    g = evaluate(p)
    assert g.feeds["depth"].state == "DEGRADED" and g.depth_mode == "QUOTE_ONLY" and g.authorized


def test_depth_error_with_stale_quotes_blocked_but_trading_allowed():
    p = retimed()
    d = fixture("sensex-depth")
    d["symbol"] = "NIFTY"
    p["depth"] = d
    for c in d["contracts"]:
        c["quote_updated_at"] = (NOW - timedelta(minutes=5)).isoformat()
    g = evaluate(p)
    assert g.feeds["depth"].state == "BLOCKED" and g.depth_mode == "UNAVAILABLE"
    assert g.authorized                             # depth is confirmation only


def test_indicator_server_fresh_overridden_by_as_of():
    p = retimed()
    ind = fixture("banknifty-indicators")
    ind["symbol"] = ind["result"]["symbol"] = "NIFTY"
    ind["result"]["last_price"] = None
    p["indicators"] = ind
    g = evaluate(p)
    fc = g.feeds["indicators"]
    assert fc.state == "BLOCKED" and any("overridden" in r for r in fc.reasons)


def test_duplicate_timestamp_noted():
    from psygrid.config import load_config
    from psygrid.data_integrity import IntegrityGate
    import helpers
    p = retimed()
    cfg = load_config()
    gate = IntegrityGate(cfg)
    orig = helpers.IntegrityGate
    helpers.IntegrityGate = lambda c: gate
    try:
        evaluate(p)
        g = evaluate(p)
    finally:
        helpers.IntegrityGate = orig
    assert any("duplicate timestamp" in r for r in g.feeds["options"].reasons)

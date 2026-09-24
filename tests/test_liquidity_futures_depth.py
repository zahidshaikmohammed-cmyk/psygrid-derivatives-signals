from datetime import datetime, timedelta

from psygrid.config import load_config
from psygrid.depth_engine import DepthEngine
from psygrid.futures_engine import FuturesEngine
from psygrid.liquidity_engine import LiquidityEngine, find_pools
from psygrid.market_clock import IST
from psygrid.schema_adapter import adapt_depth, adapt_futures
from psygrid.structure_engine import StructureEngine, Swing

from helpers import bars
from sim import fixture

T0 = datetime(2026, 9, 24, 11, 0, tzinfo=IST)
OPEN = datetime(2026, 9, 24, 9, 15, tzinfo=IST)


def _sweep_case(sign):
    """Range above a swing low at 100, then a bar that trades to 94 and closes back at 103."""
    base = [(106, 108, 104, 105), (105, 107, 101, 102), (102, 104, 100, 103), (103, 107, 102, 106),
            (106, 109, 105, 108), (108, 110, 106, 107), (107, 108, 104, 105), (105, 107, 103, 106),
            (106, 108, 104, 107), (107, 109, 105, 106), (106, 108, 104, 105), (105, 106, 103, 104),
            (104, 105, 94, 103), (103, 106, 102, 105)]
    rows = [(o, h, l, c) if sign > 0 else (200 - o, 200 - l, 200 - h, 200 - c) for o, h, l, c in base]
    b = bars(rows, start=T0)
    price = 105.5 if sign > 0 else 94.5
    st = StructureEngine(load_config()).analyze(b, price, b[-1].ts + timedelta(minutes=1, seconds=5),
                                                OPEN, OPEN + timedelta(minutes=15))
    return LiquidityEngine(load_config()).analyze(b, st, [], price, OPEN + timedelta(minutes=15)), st


def test_liquidity_sweep_of_lows_is_bullish_and_mirror_is_bearish():
    bull, st = _sweep_case(1)
    bear, _ = _sweep_case(-1)
    assert st.ready
    assert [s.direction for s in bull.sweeps] == ["BULLISH"] and bull.sweeps[0].extreme == 94
    assert [s.direction for s in bear.sweeps] == ["BEARISH"] and bear.sweeps[0].extreme == 106


def test_equal_highs_form_pool():
    sw = [Swing(T0, 100.0, "H", "1m"), Swing(T0 + timedelta(minutes=5), 100.3, "H", "1m"),
          Swing(T0, 90.0, "L", "1m")]
    pools = find_pools(sw, 0.5)
    assert len(pools) == 1 and pools[0].kind == "EQUAL_HIGHS" and pools[0].price == 100.3


def _fut(price, ts):
    p = fixture("nifty-futures")
    p.update(status="LIVE", error=None, last_price=price, updated_at=ts.isoformat())
    return adapt_futures(p, "NIFTY")[0]


def test_futures_classification_symmetric():
    for sign, expect in ((1, "STRONG_BULLISH_CONFIRMATION"), (-1, "STRONG_BEARISH_CONFIRMATION")):
        e = FuturesEngine(load_config())
        spot = 23200.0
        for i in range(5):
            s = spot + sign * 4 * i
            f = s + 60 + sign * 0.5 * i
            st = e.analyze(_fut(f, T0 + timedelta(seconds=20 * i)), True, s, 5.0, [])
        assert st.classification == expect and st.score == sign * 1.0


def test_futures_neutral_and_unavailable():
    e = FuturesEngine(load_config())
    for i in range(5):
        st = e.analyze(_fut(23260 + 0.1 * i, T0 + timedelta(seconds=20 * i)), True, 23200, 5.0, [])
    assert st.classification == "NEUTRAL"
    u = FuturesEngine(load_config()).analyze(None, False, 23200, 5.0, ["status=ERROR"])
    assert not u.available and u.score is None and u.classification == "UNAVAILABLE"


def _depth(ce_bid, ce_ask, pe_bid, pe_ask, wall=False):
    p = fixture("nifty-depth")
    for c in p["contracts"]:
        bq, aq = (ce_bid, ce_ask) if c["option_type"] == "CE" else (pe_bid, pe_ask)
        for l in c["bid"]:
            l["quantity"] = bq
        for l in c["ask"]:
            l["quantity"] = aq
        c["crossed_book"] = False
    if wall:
        p["contracts"][0]["bid"][3]["quantity"] = 10_000_000
    return adapt_depth(p, "NIFTY")[0]


def test_depth_bullish_and_bearish_symmetry():
    e = DepthEngine(load_config())
    bull = e.analyze(_depth(2000, 1000, 1000, 2000), "FULL", 23250.0, 50.0)
    bear = DepthEngine(load_config()).analyze(_depth(1000, 2000, 2000, 1000), "FULL", 23250.0, 50.0)
    assert bull.score > 0 and bear.score < 0 and abs(bull.score + bear.score) < 1e-9


def test_depth_wall_is_only_a_note():
    d = DepthEngine(load_config()).analyze(_depth(1000, 1000, 1000, 1000, wall=True), "FULL", 23250.0, 50.0)
    assert any("wall" in w for w in d.walls)
    assert abs(d.score) <= 1.0


def test_depth_quote_only_halved_and_unavailable():
    p = fixture("sensex-depth")
    dd = adapt_depth(p, "SENSEX")[0]
    q = DepthEngine(load_config()).analyze(dd, "QUOTE_ONLY", 74100.0, 100.0)
    assert q.mode == "QUOTE_ONLY" and q.score is not None and abs(q.score) <= 0.5
    u = DepthEngine(load_config()).analyze(dd, "UNAVAILABLE", 74100.0, 100.0)
    assert u.score is None

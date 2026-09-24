from datetime import datetime, timedelta

from psygrid.config import load_config
from psygrid.market_clock import IST
from psygrid.structure_engine import StructureEngine, find_swings, segments
from psygrid.underlying_engine import UnderlyingTracker, aggregate

from helpers import bars, line_bars

T0 = datetime(2026, 9, 24, 10, 0, tzinfo=IST)
OPEN = datetime(2026, 9, 24, 9, 15, tzinfo=IST)


def test_tracker_rejects_duplicates_out_of_order_and_jumps():
    t = UnderlyingTracker("NIFTY", None, max_jump_pct=2.0)
    assert t.add_observation(T0, 23200, "X")
    assert not t.add_observation(T0, 23201, "X")                         # duplicate timestamp
    assert not t.add_observation(T0 - timedelta(seconds=5), 23201, "X")  # out of order
    assert not t.add_observation(T0 + timedelta(seconds=20), 25000, "X") # impossible jump
    assert t.add_observation(T0 + timedelta(seconds=20), 23210, "X")
    assert len(t.obs) == 2 and t.rejected


def test_internal_bars_are_labelled_and_current_minute_incomplete():
    t = UnderlyingTracker("NIFTY")
    for i, p in enumerate([100, 102, 99, 101, 103, 104]):
        t.add_observation(T0 + timedelta(seconds=20 * i), 23000 + p, "OPTION_CHAIN.underlying_ltp")
    b = t.bars_1m(T0 + timedelta(seconds=110))
    assert [x.source for x in b] == ["INTERNAL_AGG_1m"] * 2
    assert b[0].complete and not b[1].complete
    assert b[0].high == 23102 and b[0].low == 23099 and b[0].volume is None and b[0].observations == 3


def test_persistence_reload_same_day(tmp_path):
    t = UnderlyingTracker("NIFTY", tmp_path)
    t.add_observation(T0, 23200, "X")
    t.add_observation(T0 + timedelta(seconds=20), 23205, "X")
    t2 = UnderlyingTracker("NIFTY", tmp_path)
    assert t2.load_day("2026-09-24") == 2 and t2.last.price == 23205
    assert UnderlyingTracker("NIFTY", tmp_path).load_day("2026-09-25") == 0


def test_aggregate_requires_fill_and_never_invents_bars():
    b = line_bars([100 + i for i in range(10)], start=datetime(2026, 9, 24, 10, 0, tzinfo=IST))
    five = aggregate(b, 5, 0.8, "INTERNAL_AGG_5m")
    assert len(five) == 2 and five[0].ts.minute == 0 and five[0].source == "INTERNAL_AGG_5m"
    sparse = [b[0], b[1], b[5], b[6], b[7], b[8], b[9]]
    assert len(aggregate(sparse, 5, 0.8, "X")) == 1             # first bucket only 2/5 bars -> dropped


def test_segments_split_on_gap():
    b = bars([(1, 2, 0.5, 1.5)] * 3) + bars([(1, 2, 0.5, 1.5)] * 2, start=T0 + timedelta(minutes=60))
    assert [len(s) for s in segments(b)] == [3, 2]


def test_swings_fractal():
    b = line_bars([10, 12, 14, 16, 14, 12, 10, 12, 14], spread=0.1)
    kinds = [(s.kind, round(s.price, 1)) for s in find_swings(b, 2, "1m")]
    assert ("H", 16.1) in kinds and ("L", 9.9) in kinds


def _analyze(closes):
    eng = StructureEngine(load_config())
    b = line_bars(closes, spread=1.0)
    now = b[-1].ts + timedelta(minutes=1, seconds=5)
    return eng.analyze(b, closes[-1], now, OPEN, OPEN + timedelta(minutes=15))


def test_trend_detection_is_symmetric():
    up = [100, 104, 108, 104, 101, 106, 111, 116, 111, 108, 113, 118, 123, 118, 115, 120, 126, 131]
    down = [200 - x for x in up]
    su, sd = _analyze(up), _analyze(down)
    assert su.ready and sd.ready
    assert su.trend == "UP" and sd.trend == "DOWN"
    assert abs(su.momentum + sd.momentum) < 1e-9
    assert su.high_seq == "HH" and su.low_seq == "HL" and sd.high_seq == "LH" and sd.low_seq == "LL"


def test_warming_up_when_insufficient_bars():
    s = _analyze([100, 101, 102])
    assert not s.ready and "warming up" in s.reason


def test_opening_range_incomplete_is_reported():
    eng = StructureEngine(load_config())
    b = bars([(100, 101, 99, 100)] * 3, start=OPEN)
    s = eng.analyze(b, 100, OPEN + timedelta(minutes=60), OPEN, OPEN + timedelta(minutes=15))
    assert not s.or_complete and any("opening range incomplete" in n for n in s.notes)


def test_feed_candle_in_progress_is_incomplete():
    from psygrid.schema_adapter import adapt_spot
    from sim import fixture
    p = fixture("banknifty")
    spot, _ = adapt_spot(p, "BANKNIFTY")
    t = UnderlyingTracker("BANKNIFTY")
    t.update_feed_candles(spot)
    during = t.bars_1m(datetime(2026, 9, 24, 9, 16, 30, tzinfo=IST))
    after = t.bars_1m(datetime(2026, 9, 24, 9, 20, tzinfo=IST))
    assert [b.complete for b in during] == [True, False]
    assert all(b.complete for b in after) and all(b.source == "FEED_1m" for b in after)

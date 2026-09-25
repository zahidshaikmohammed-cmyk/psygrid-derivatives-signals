"""Setup engine: event -> setup mapping, symmetry and context filters."""

from datetime import datetime, timedelta

from psygrid.config import load_config
from psygrid.level_engine import LevelEvent, LevelMap, Zone
from psygrid.liquidity_engine import LiquidityState, SweepEvent
from psygrid.market_clock import IST
from psygrid.models import Candle
from psygrid.setup_engine import SetupEngine
from psygrid.structure_engine import StructureState, Swing

NOW = datetime(2026, 9, 24, 11, 30, tzinfo=IST)


def st(trend="RANGE", momentum=0.0, vwap=None, **kw):
    s = StructureState(ready=True, bars=30, price=0, avg_range=5.0, trend=trend, momentum=momentum)
    s.vwap = vwap
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def zone(center, state, event, direction, tier=1, strength=70, families=("SWING", "PREV_DAY"), **kw):
    z = Zone(id=f"NIFTY_L_{int(center) % 1000:03d}", low=center - 2, high=center + 2, center=center,
             strength=strength, tier=tier, families=list(families), state=state, state_ts=NOW - timedelta(seconds=30))
    z.events = [LevelEvent(NOW - timedelta(seconds=30), event, direction, center)]
    for k, v in kw.items():
        setattr(z, k, v)
    return z


def last_bar(up=True):
    o, c = (100, 104) if up else (104, 100)
    return [Candle(NOW - timedelta(minutes=2), o, 105, 99, c, None, "T")]


def detect(price, zones, s=None, sweeps=(), bars=None):
    lm = LevelMap(zones=zones, price=price)
    return SetupEngine(load_config()).detect(price, NOW, s or st(), lm, LiquidityState(sweeps=list(sweeps)),
                                             bars or last_bar(True))


def test_breakout_acceptance_call_and_breakdown_put_mirror():
    call = detect(23506, [zone(23500, "ACCEPTED", "ACCEPTED", "UP", accepted_dir="UP")])
    put = detect(23494, [zone(23500, "ACCEPTED", "ACCEPTED", "DOWN", accepted_dir="DOWN")])
    assert [(c.direction, c.setup) for c in call.candidates] == [("CALL", "BREAKOUT + ACCEPTANCE")]
    assert [(c.direction, c.setup) for c in put.candidates] == [("PUT", "BREAKDOWN + ACCEPTANCE")]
    assert call.candidates[0].invalidation < 23498 and put.candidates[0].invalidation > 23502
    assert call.candidates[0].quality == put.candidates[0].quality


def test_no_chasing_after_extended_breakout():
    r = detect(23560, [zone(23500, "ACCEPTED", "ACCEPTED", "UP", accepted_dir="UP")])
    assert not r.candidates and any("no chasing" in w for w in r.waiting)


def test_failed_breakout_put_and_failed_breakdown_call():
    fb = detect(23493, [zone(23500, "FAILED_BREAKOUT", "FAILED_BREAKOUT", "DOWN", break_extreme=23512)])
    fd = detect(23507, [zone(23500, "FAILED_BREAKDOWN", "FAILED_BREAKDOWN", "UP", break_extreme=23488)])
    assert fb.candidates[0].direction == "PUT" and fb.candidates[0].setup == "FAILED BREAKOUT"
    assert fb.candidates[0].invalidation > 23512
    assert fd.candidates[0].direction == "CALL" and fd.candidates[0].setup == "FAILED BREAKDOWN"
    assert fd.candidates[0].invalidation < 23488


def test_support_bounce_requires_confirming_close():
    z = zone(23400, "REJECTED", "REJECTED", "UP", families=("SWING",), strength=50, tier=2)
    ok = detect(23410, [z], bars=last_bar(True))
    no = detect(23410, [z], bars=last_bar(False))
    assert ok.candidates[0].setup == "SUPPORT BOUNCE" and ok.candidates[0].direction == "CALL"
    assert not no.candidates and any("confirming close" in w for w in no.waiting)


def test_resistance_rejection_put():
    z = zone(23500, "REJECTED", "REJECTED", "DOWN", families=("SWING",), strength=50, tier=2)
    r = detect(23490, [z], bars=last_bar(False))
    assert r.candidates[0].setup == "RESISTANCE REJECTION" and r.candidates[0].direction == "PUT"


def test_chase_limited_failed_breakout_is_still_observable():
    """Pre-scoring starvation audit: previously only ACCEPTED/RECLAIMED/
    RETEST_HELD produced a 'no chasing' waiting message when the event was
    chase-limited - a FAILED_BREAKOUT/FAILED_BREAKDOWN (or a bare REJECTED)
    the level engine had genuinely detected vanished with zero trace: no
    candidate, no rejected reason, no waiting message. The chase limit
    itself (no candidate) is unchanged here; only its visibility is fixed."""
    r = detect(23480, [zone(23500, "FAILED_BREAKOUT", "FAILED_BREAKOUT", "DOWN", break_extreme=23512)])
    assert not r.candidates
    assert any("no chasing" in w and "failed breakout" in w.lower() for w in r.waiting)


def test_chase_limited_rejected_event_is_still_observable():
    z = zone(23500, "REJECTED", "REJECTED", "DOWN", families=("SWING",), strength=50, tier=2)
    r = detect(23480, [z], bars=last_bar(False))
    assert not r.candidates
    assert any("no chasing" in w and "rejected" in w.lower() for w in r.waiting)


def test_bullish_liquidity_sweep_reclaim_and_bearish_mirror():
    """Replay-fixture audit: LiquidityEngine's sweep detection was already
    unit-tested (test_liquidity_futures_depth.py) for both directions, but
    the setup_engine mapping from a SweepEvent to a LIQUIDITY SWEEP +
    RECLAIM candidate had zero coverage anywhere - not even a unit test."""
    bull_sweep = SweepEvent(direction="BULLISH", ref_price=23400, ref_label="swing low 23400",
                            ref_zone_id=None, extreme=23390, sweep_ts=NOW - timedelta(minutes=1),
                            confirm_ts=NOW - timedelta(seconds=30), age_bars=1)
    bear_sweep = SweepEvent(direction="BEARISH", ref_price=23400, ref_label="swing high 23400",
                            ref_zone_id=None, extreme=23410, sweep_ts=NOW - timedelta(minutes=1),
                            confirm_ts=NOW - timedelta(seconds=30), age_bars=1)
    call = detect(23405, [], sweeps=[bull_sweep])
    put = detect(23395, [], sweeps=[bear_sweep])
    assert call.candidates[0].setup == "LIQUIDITY SWEEP + RECLAIM" and call.candidates[0].direction == "CALL"
    assert call.candidates[0].invalidation < 23390
    assert put.candidates[0].setup == "LIQUIDITY SWEEP + RECLAIM" and put.candidates[0].direction == "PUT"
    assert put.candidates[0].invalidation > 23410


def test_multi_factor_level_reaction():
    z = zone(23400, "REJECTED", "REJECTED", "UP", families=("SWING", "PREV_DAY", "OPTIONS"), strength=85)
    r = detect(23410, [z])
    assert r.candidates[0].setup == "MULTI-FACTOR LEVEL REACTION"


def test_retest_held_breakout_retest():
    z = zone(23500, "REJECTED", "REJECTED", "UP", accepted_dir="UP")
    z.events.append(LevelEvent(NOW - timedelta(seconds=30), "RETEST_HELD", "UP", 23508))
    r = detect(23508, [z])
    assert r.candidates[0].setup == "BREAKOUT + RETEST" and r.candidates[0].direction == "CALL"


def test_liquidity_sweep_both_directions():
    bull = SweepEvent("BULLISH", 23400, "swing low", None, 23392, NOW - timedelta(minutes=2), NOW, 1)
    bear = SweepEvent("BEARISH", 23500, "swing high", None, 23508, NOW - timedelta(minutes=2), NOW, 1)
    r1 = detect(23404, [], sweeps=[bull])
    r2 = detect(23496, [], sweeps=[bear])
    assert r1.candidates[0].setup == "LIQUIDITY SWEEP + RECLAIM" and r1.candidates[0].direction == "CALL"
    assert r2.candidates[0].direction == "PUT" and r2.candidates[0].invalidation > 23508


def test_call_blocked_directly_under_major_resistance():
    sup = zone(23400, "REJECTED", "REJECTED", "UP", families=("SWING",), strength=50, tier=2)
    res = zone(23420, "APPROACHING", "APPROACHING", None, tier=1, strength=90)
    r = detect(23410, [sup, res])
    assert not r.candidates
    assert any("MAJOR RESISTANCE" in w and "BREAKOUT + ACCEPTANCE" in w for w in r.waiting)


def test_wait_for_acceptance_while_break_pending():
    pending = zone(23500, "BROKEN", "BROKEN", "UP", break_dir="UP")
    s = st(trend="UP", momentum=2.0, expansion=True,
           swing_lows=[Swing(NOW - timedelta(minutes=5), 23480, "L", "1m")],
           swing_highs=[Swing(NOW - timedelta(minutes=8), 23495, "H", "1m")])
    r = detect(23506, [pending], s=s)
    assert not r.candidates and any("WAIT FOR ACCEPTANCE" in w for w in r.waiting)


def test_momentum_continuation_symmetric():
    up = st(trend="UP", momentum=2.0, expansion=True, swing_lows=[Swing(NOW, 23480, "L", "1m")])
    dn = st(trend="DOWN", momentum=-2.0, expansion=True, swing_highs=[Swing(NOW, 23520, "H", "1m")])
    a = detect(23500, [], s=up)
    b = detect(23500, [], s=dn)
    assert a.candidates[0].setup == b.candidates[0].setup == "MOMENTUM CONTINUATION"
    assert a.candidates[0].direction == "CALL" and b.candidates[0].direction == "PUT"
    assert a.candidates[0].quality == b.candidates[0].quality


def test_vwap_reclaim_and_loss():
    bars_up = [Candle(NOW - timedelta(minutes=4 - i), c - 1, c + 1, c - 2, c, None, "T")
               for i, c in enumerate([98, 99, 101, 103])]
    bars_dn = [Candle(b.ts, 200 - b.open, 200 - b.low, 200 - b.high, 200 - b.close, None, "T") for b in bars_up]
    a = SetupEngine(load_config()).detect(103.5, NOW, st(vwap=100.0), LevelMap([], 103.5), LiquidityState(), bars_up)
    b = SetupEngine(load_config()).detect(96.5, NOW, st(vwap=100.0), LevelMap([], 96.5), LiquidityState(), bars_dn)
    assert ("CALL", "VWAP RECLAIM") in [(c.direction, c.setup) for c in a.candidates]
    assert ("PUT", "VWAP RECLAIM") in [(c.direction, c.setup) for c in b.candidates]


def test_structure_not_ready_waits():
    s = StructureState(ready=False, reason="warming up: 3/12")
    r = SetupEngine(load_config()).detect(100, NOW, s, LevelMap([], 100), LiquidityState(), [])
    assert not r.candidates and "warming up" in r.waiting[0]

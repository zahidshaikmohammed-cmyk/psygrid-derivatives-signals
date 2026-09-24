"""Intelligent level engine: clustering, strength, tiers and the state machine."""

from datetime import datetime, timedelta

from psygrid.config import load_config
from psygrid.level_engine import Candidate, LevelEngine
from psygrid.market_clock import IST
from psygrid.models import Candle

T0 = datetime(2026, 9, 24, 11, 0, tzinfo=IST)


def eng():
    return LevelEngine(load_config(), "NIFTY")


def test_nearby_prices_cluster_into_one_zone():
    e = eng()
    cands = [Candidate(p, "SWING", "1m swing high", "1m", 8, T0) for p in (23496, 23499, 23502, 23505)]
    groups = e.cluster(cands, 23450)
    assert len(groups) == 1
    lm = e.update(23450, T0, cands, [], 5.0)
    assert len(lm.zones) == 1
    z = lm.zones[0]
    assert z.low <= 23496 and z.high >= 23505 and 23496 <= z.center <= 23505
    assert z.id == "NIFTY_L_001"


def test_far_prices_do_not_cluster():
    e = eng()
    cands = [Candidate(p, "SWING", "s", "1m", 8) for p in (23400, 23500)]
    assert len(e.cluster(cands, 23450)) == 2


def test_confluence_raises_strength_and_tier():
    e = eng()
    single = [Candidate(23500, "SWING", "1m swing high", "1m", 8, T0)]
    lm1 = e.update(23450, T0, single, [], 5.0)
    s1, t1 = lm1.zones[0].strength, lm1.zones[0].tier
    e2 = eng()
    multi = single + [Candidate(23501, "PDH", "Prev day high", "DAILY", 22),
                      Candidate(23500, "OI_CE", "CE OI", "OPTIONS", 18),
                      Candidate(23499, "SWING", "5m swing high", "5m", 12, T0),
                      Candidate(23500, "ROUND", "Round", "STATIC", 7)]
    z = e2.update(23450, T0, multi, [], 5.0).zones[0]
    assert z.strength > s1 + 40 and z.tier == 1 and t1 == 3
    assert "PREV_DAY" in z.families and "OPTIONS" in z.families and z.timeframe == "DAILY"


def test_option_oi_alone_is_not_major():
    e = eng()
    z = e.update(23450, T0, [Candidate(23500, "OI_CE", "CE OI", "OPTIONS", 18)], [], 5.0).zones[0]
    assert z.tier == 3


def _drive(e, cands, path, start=T0, step=20):
    """Feed prices every ``step`` s and completed 1m bars built from them."""
    obs = []
    lm = None
    for i, p in enumerate(path):
        now = start + timedelta(seconds=step * i)
        obs.append((now, p))
        minute = {}
        for t, q in obs:
            minute.setdefault(t.replace(second=0), []).append(q)
        cur = now.replace(second=0)
        closed = [Candle(m, v[0], max(v), min(v), v[-1], None, "T") for m, v in sorted(minute.items()) if m < cur]
        lm = e.update(p, now, cands, closed, 5.0)
    return lm


LEVEL = [Candidate(23500, "SWING", "swing", "1m", 30, T0 - timedelta(hours=1)),
         Candidate(23500, "PDH", "pdh", "DAILY", 22)]


def states(lm):
    return [ev.event for ev in lm.zones[0].events]


def test_approach_test_reject():
    e = eng()
    lm = _drive(e, LEVEL, [23470, 23485, 23492, 23498, 23500, 23496, 23489, 23480])
    ev = states(lm)
    assert "APPROACHING" in ev and "TESTING" in ev and ev[-1] == "REJECTED"
    assert lm.zones[0].events[-1].direction == "DOWN" and lm.zones[0].rejections == 1


def test_breakout_then_acceptance():
    e = eng()
    path = [23480, 23490, 23499, 23505] + [23512] * 12
    lm = _drive(e, LEVEL, path)
    z = lm.zones[0]
    assert "BROKEN" in states(lm) and z.state == "ACCEPTED" and z.accepted_dir == "UP"
    assert z.kind == "SUPPORT" and "→" in z.role_label


def test_breakout_then_failed_breakout():
    e = eng()
    path = [23480, 23490, 23499, 23506, 23508, 23503, 23496, 23488, 23480]
    lm = _drive(e, LEVEL, path)
    assert "BROKEN" in states(lm) and "FAILED_BREAKOUT" in states(lm)
    assert lm.zones[0].events[-1].direction == "DOWN" or lm.zones[0].state == "FAILED_BREAKOUT"


def test_breakdown_failure_is_mirror():
    e = eng()
    level = [Candidate(23500, "SWING", "swing", "1m", 30, T0 - timedelta(hours=1)),
             Candidate(23500, "PDL", "pdl", "DAILY", 22)]
    path = [23520, 23510, 23501, 23494, 23492, 23497, 23504, 23512, 23520]
    lm = _drive(e, level, path)
    assert "BROKEN" in states(lm) and "FAILED_BREAKDOWN" in states(lm)


def test_accepted_then_retest_held():
    e = eng()
    path = [23480, 23490, 23499, 23505] + [23512] * 12 + [23506, 23501, 23499, 23506, 23512, 23516]
    lm = _drive(e, LEVEL, path)
    ev = states(lm)
    assert "ACCEPTED" in ev and "RETEST_HELD" in ev


def test_reclaimed_after_opposite_acceptance():
    e = eng()
    path = ([23480, 23490, 23499, 23505] + [23512] * 12 +          # accepted above
            [23505, 23499, 23494] + [23486] * 12 +                  # accepted below
            [23495, 23500, 23505] + [23513] * 12)                   # back above -> RECLAIMED
    lm = _drive(e, LEVEL, path)
    assert "RECLAIMED" in states(lm)


def test_stable_ids_across_cycles():
    e = eng()
    lm1 = e.update(23450, T0, LEVEL, [], 5.0)
    lm2 = e.update(23452, T0 + timedelta(seconds=20),
                   LEVEL + [Candidate(23503, "ROUND", "r", "STATIC", 3)], [], 5.0)
    assert lm1.zones[0].id == lm2.zones[0].id


def test_retest_after_approach_still_recognised():
    e = eng()
    path = ([23480, 23490, 23499, 23505] + [23512] * 12 +      # accepted above
            [23530] * 20 +                                      # move away (acceptance event ages)
            [23512, 23507, 23501, 23507, 23514, 23520])         # approach, retest, hold
    lm = _drive(e, LEVEL, path)
    assert "RETEST_HELD" in states(lm)


def test_second_break_after_failure_is_reclaimed():
    e = eng()
    path = ([23480, 23490, 23499, 23506, 23503, 23496, 23488, 23480] +   # failed breakout
            [23490, 23499, 23505] + [23513] * 12)                          # accepted on 2nd try
    lm = _drive(e, LEVEL, path)
    ev = states(lm)
    assert "FAILED_BREAKOUT" in ev and ev.count("RECLAIMED") == 1

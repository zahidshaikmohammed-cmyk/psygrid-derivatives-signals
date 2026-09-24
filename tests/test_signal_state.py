from datetime import datetime, timedelta

from psygrid.config import load_config
from psygrid.market_clock import IST
from psygrid.signal_state import Signal, SignalStateManager

T0 = datetime(2026, 9, 24, 11, 0, tzinfo=IST)


def sig(direction="CALL", strike=23200.0, setup="BREAKOUT + ACCEPTANCE", score=80.0, u=23220.0,
        inv=23200.0, t1=23260.0, t2=23290.0, created=T0):
    d = 1 if direction == "CALL" else -1
    if d < 0:
        inv, t1, t2 = 2 * u - inv, 2 * u - t1, 2 * u - t2
    return Signal(id="x", index="NIFTY", direction=direction, strike=strike,
                  option_type="CE" if d > 0 else "PE", setup=setup, key_level_id="NIFTY_L_001",
                  key_level_price=23200, level_type="R", level_strength=80, market_state="", underlying=u,
                  underlying_source="t", option_ltp=100, bid=99.9, ask=100.1, spread_pct=0.2, entry_low=98,
                  entry_high=102, invalidation=inv, t1=t1, t2=t2, option_invalidation=None, option_t1=None,
                  option_t2=None, reward_risk=2, target_basis="", holding="", max_hold_minutes=40, score=score,
                  grade="SIGNAL", confirmations=[], evidence=[], strike_reasons=[], notes=[], created=created)


def test_dedup_same_direction_not_repeated():
    m = SignalStateManager(load_config())
    ok, _, ev = m.consider(sig(), T0)
    assert ok and ev[0].event == "SIGNAL"
    ok2, why, _ = m.consider(sig(strike=23250.0), T0 + timedelta(seconds=20))
    assert not ok2 and "already active" in why


def test_targets_then_close():
    m = SignalStateManager(load_config())
    m.consider(sig(), T0)
    ev = m.track("NIFTY", 23262, T0 + timedelta(minutes=2), False)
    assert [e.event for e in ev] == ["TARGET_1"] and m.state_of("NIFTY") == "TARGET_1"
    assert m.active["NIFTY"].stop == 23220 and m.active["NIFTY"].invalidation == 23200
    ev = m.track("NIFTY", 23291, T0 + timedelta(minutes=4), False)
    assert [e.event for e in ev] == ["TARGET_2", "CLOSED"] and m.state_of("NIFTY") == "FLAT"


def test_invalidation_and_cooldown():
    m = SignalStateManager(load_config())
    m.consider(sig(), T0)
    ev = m.track("NIFTY", 23199, T0 + timedelta(minutes=1), False)
    assert [e.event for e in ev] == ["INVALIDATED", "CLOSED"]
    ok, why, _ = m.consider(sig(setup="SUPPORT BOUNCE"), T0 + timedelta(minutes=2))
    assert not ok and "cooldown" in why
    ok, _, _ = m.consider(sig(setup="SUPPORT BOUNCE"), T0 + timedelta(minutes=20))
    assert ok


def test_put_invalidation_symmetric():
    m = SignalStateManager(load_config())
    m.consider(sig("PUT"), T0)
    ev = m.track("NIFTY", 23241, T0 + timedelta(minutes=1), False)
    assert ev[0].event == "INVALIDATED"


def test_opposing_signal_closes_active():
    m = SignalStateManager(load_config())
    m.consider(sig(), T0)
    ok, _, ev = m.consider(sig("PUT"), T0 + timedelta(minutes=3))
    assert ok and ev[0].event == "CLOSED" and m.active["NIFTY"].direction == "PUT"


def test_time_stop_and_session_close():
    m = SignalStateManager(load_config())
    m.consider(sig(), T0)
    ev = m.track("NIFTY", 23225, T0 + timedelta(minutes=41), False)
    assert ev[-1].event == "CLOSED" and "time stop" in ev[-1].text
    m.consider(sig(setup="OTHER"), T0 + timedelta(minutes=50))
    ev = m.track("NIFTY", 23225, T0 + timedelta(minutes=51), True)
    assert ev[-1].event == "CLOSED" and "session close" in ev[-1].text

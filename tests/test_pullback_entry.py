"""Entry architecture: no chasing for level-anchored setups, no lost signals
for continuation setups, and an explicit entry state for every opportunity.

The pipeline runs for real (data gate, underlying tracker, 1m bars, structure,
level map, strike selector, risk engine, lifecycle, Telegram wiring) on the
deterministic simulator. Only setup DETECTION and the confluence SCORE are
pinned by the test so that every setup name can be exercised in both
directions on controlled price paths; neither stub bypasses any gate.
"""

import math
from datetime import datetime, timedelta

import pytest

import run_engine
from psygrid.config import load_config
from psygrid.data_integrity import IntegrityGate
from psygrid.level_engine import LevelMap
from psygrid.market_clock import IST, MarketClock
from psygrid.models import Candle
from psygrid.risk_engine import RiskEngine
from psygrid.scoring_engine import ScoreResult
from psygrid.setup_engine import BASE_QUALITY, SetupCandidate, SetupResult
from psygrid.signal_engine import (CANCELLED, EXPIRED, NO_SETUP, PULLBACK_RECEIVED, RISK_REJECTED,
                                   SETUP_DETECTED, SIGNAL_AUTHORIZED, SIGNAL_GRADE_BLOCKED, SUPPRESSED,
                                   WAITING_FOR_PULLBACK, IndexPipeline, PsygridEngine, pullback_eligible)
from sim import SimMarket

C = 23200.0
MOMENTUM = ("BREAKOUT + ACCEPTANCE", "BREAKDOWN + ACCEPTANCE", "MOMENTUM CONTINUATION", "VWAP RECLAIM")
LEVEL_ANCHORED = ("BREAKOUT + RETEST", "BREAKDOWN + RETEST", "LIQUIDITY SWEEP + RECLAIM",
                  "MULTI-FACTOR LEVEL REACTION", "FAILED BREAKOUT", "FAILED BREAKDOWN", "SUPPORT BOUNCE",
                  "RESISTANCE REJECTION", "RANGE EXTREME REVERSAL", "VWAP REJECTION")

# ------------------------------------------------------------------ paths
# Bull frame (CALL); SimMarket(sign=-1) mirrors every price around 23200 for
# the PUT twin. One point per 20 s poll; t in minutes. Quiet chop for warm-up,
# a 30-pt burst away from the level (23205) between t=16 and t=18, then:


def _chop(t):
    return C + 3 * math.sin(t * 1.7) + 2 * math.sin(t * 4.1)


def _burst(t):
    return C + 5 + 12.5 * (t - 16)            # 23205 -> 23230 at t=18


def path_pullback(i):                          # retraces to 23214 by t=22, then resumes
    t = i / 3.0
    if t < 16:
        return _chop(t), "range"
    if t < 18:
        return _burst(t), "breakout"
    if t < 22:
        return 23230 - 4 * (t - 18), "hold"
    return 23214 + 2 * (t - 22), "trend"


def path_no_pullback(i):                       # keeps running: never gives 38% back
    t = i / 3.0
    if t < 16:
        return _chop(t), "range"
    if t < 18:
        return _burst(t), "breakout"
    return 23230 + 3 * (t - 18), "trend"


def path_delayed_pullback(i):                  # sits at the high 9 min, then pulls back
    t = i / 3.0
    if t < 16:
        return _chop(t), "range"
    if t < 18:
        return _burst(t), "breakout"
    if t < 27:
        return 23230 + 0.8 * math.sin(t * 2), "hold"
    if t < 29:
        return 23230 - 8 * (t - 27), "hold"
    return 23214 + 2 * (t - 29), "trend"


def path_through_invalidation(i):              # one-tick collapse through the stop
    t = i / 3.0
    if t < 16:
        return _chop(t), "range"
    if t < 18:
        return _burst(t), "breakout"
    if t < 19:
        return 23230, "hold"
    return 23185, "hold"


# ---------------------------------------------------------------- harness
def run(path, setup, sign, detect_from=18.0, detect_for=40.0, cycles=120, score=80.0,
        entries_allowed=None, cand_hook=None, risk_error=None):
    """Run the real engine; setup ``setup`` is detected (in the bull frame at
    level 23205, invalidation 23197) from ``detect_from`` for ``detect_for``
    minutes. Returns [(t_minutes, decision, events)]."""
    cfg = load_config()
    eng = PsygridEngine(cfg, indices=("NIFTY",))
    pipe = eng.pipes["NIFTY"]
    sim = SimMarket(path, sign=sign)
    t0 = sim.start
    mirror = (lambda p: p) if sign > 0 else (lambda p: 2 * C - p)
    direction = "CALL" if sign > 0 else "PUT"

    def detect(price, now, st, lm, liq, bars):
        t = (now - t0).total_seconds() / 60
        if not st.ready or not (detect_from <= t < detect_from + detect_for):
            return SetupResult([], [], [])
        c = SetupCandidate(direction, setup, None, mirror(23205.0), mirror(23197.0),
                           BASE_QUALITY[setup], "TEST", ["test"], now)
        if cand_hook:
            c = cand_hook(c, t)
        return SetupResult([c] if c else [], [], [])

    pipe.setups.detect = detect
    pipe.scoring.score = lambda comps: ScoreResult(score, "SIGNAL" if score >= 75 else "WATCH", comps,
                                                   ["futures", "options"], [])
    risk = RiskEngine(cfg)
    pipe.risk.plan = (lambda c, sel, lm, price, m: (None, risk_error)) if risk_error else \
        (lambda c, sel, lm, price, m: risk.plan(c, sel, LevelMap([], price), price, m))
    if entries_allowed is not None:
        eng.clock.entries_allowed = entries_allowed
        for p in eng.pipes.values():
            p.clock = eng.clock
    out = []
    for _ in range(cycles):
        raws, now, _, _ = sim.step_raws()
        res = eng.cycle(raws, local_now=now)
        out.append(((now - t0).total_seconds() / 60, res.decisions["NIFTY"], res.events))
    return out


def emitted(out):
    return [(t, d) for t, d, _ in out if d.signal is not None]


def states(out):
    return [d.entry_state for _, d, _ in out]


# ------------------------------------------------------------ taxonomy
def test_policy_follows_the_existing_setup_families():
    for name in MOMENTUM:
        assert not pullback_eligible(SetupCandidate("CALL", name, None, 0, 0, 0.5, ""))
    for name in LEVEL_ANCHORED:
        assert pullback_eligible(SetupCandidate("CALL", name, None, 0, 0, 0.5, ""))
    assert set(MOMENTUM) | set(LEVEL_ANCHORED) == set(BASE_QUALITY)


# ------------------------------------- 1-4: continuation is never lost
@pytest.mark.parametrize("setup,sign", [("BREAKOUT + ACCEPTANCE", 1), ("BREAKDOWN + ACCEPTANCE", -1),
                                        ("MOMENTUM CONTINUATION", 1), ("MOMENTUM CONTINUATION", -1),
                                        ("VWAP RECLAIM", 1), ("VWAP RECLAIM", -1)])
def test_continuation_enters_immediately_even_if_price_never_pulls_back(setup, sign):
    out = run(path_no_pullback, setup, sign)
    sig = emitted(out)
    assert len(sig) == 1
    t, d = sig[0]
    assert t < 18.5, "continuation must enter on detection, not wait"
    assert d.entry_state == SIGNAL_AUTHORIZED
    assert d.signal.direction == ("CALL" if sign > 0 else "PUT")
    assert WAITING_FOR_PULLBACK not in states(out)


# ------------------ 5, 9-14: every level-anchored setup, both directions
@pytest.mark.parametrize("setup", LEVEL_ANCHORED)
@pytest.mark.parametrize("sign", [1, -1])
def test_level_anchored_waits_then_enters_on_the_pullback(setup, sign):
    out = run(path_pullback, setup, sign)
    arm = next(t for t, d, _ in out if d.entry_state == WAITING_FOR_PULLBACK)
    assert 18.0 <= arm < 18.5, "armed at the burst extreme instead of chasing it"
    sig = emitted(out)
    assert len(sig) == 1
    t, d = sig[0]
    assert d.entry_state == PULLBACK_RECEIVED and t > arm
    s = d.signal
    assert s.direction == ("CALL" if sign > 0 else "PUT")
    burst_top = 23230 if sign > 0 else 2 * C - 23230
    assert (burst_top - s.underlying) * (1 if sign > 0 else -1) >= 0.382 * 20, "entry is on the pullback"
    assert s.invalidation == (23197.0 if sign > 0 else 2 * C - 23197.0), "stop unchanged"
    assert "Entered on pullback" in s.evidence[0]


# ---------------------------- 6: no pullback -> explicit expiry, no chase
@pytest.mark.parametrize("setup", ["MULTI-FACTOR LEVEL REACTION", "BREAKDOWN + RETEST", "FAILED BREAKOUT"])
@pytest.mark.parametrize("sign", [1, -1])
def test_level_anchored_without_pullback_expires_explicitly(setup, sign):
    out = run(path_no_pullback, setup, sign)
    assert emitted(out) == []
    st = states(out)
    i = st.index(WAITING_FOR_PULLBACK)
    j = st.index(EXPIRED)
    t_arm, t_exp = out[i][0], out[j][0]
    assert 15.0 <= t_exp - t_arm <= 15.4, "window is bounded; re-arming never extends it"
    assert all(s == WAITING_FOR_PULLBACK for s in st[i:j])
    # the same opportunity keeps being detected but is never chased afterwards
    after = [d for t, d, _ in out if t > t_exp + 0.1]
    assert after and all(d.entry_state == EXPIRED and d.signal is None for d in after)
    assert "entry location lost" in after[0].entry_detail


# ------------------------------------ 7: pullback after a realistic delay
@pytest.mark.parametrize("sign", [1, -1])
def test_pullback_after_a_realistic_delay_still_fills(sign):
    out = run(path_delayed_pullback, "SUPPORT BOUNCE" if sign > 0 else "RESISTANCE REJECTION", sign)
    sig = emitted(out)
    assert len(sig) == 1 and 27.0 <= sig[0][0] <= 30.0
    assert sig[0][1].entry_state == PULLBACK_RECEIVED
    # while flat at the high (burst no longer "fresh") it did NOT slip out at the high
    flat = [d for t, d, _ in out if 22.5 <= t < 27.0]
    assert flat and all(d.entry_state == WAITING_FOR_PULLBACK and d.signal is None for d in flat)


# ---------------------------------------- 8: invalidation before pullback
@pytest.mark.parametrize("sign", [1, -1])
def test_move_through_invalidation_cancels_without_a_signal(sign):
    out = run(path_through_invalidation, "LIQUIDITY SWEEP + RECLAIM", sign, detect_for=1.0)
    assert emitted(out) == []
    d = next(d for _, d, _ in out if d.entry_state == CANCELLED)
    assert "invalidation" in d.entry_detail


# --------------------------------------------- 15: dedup / cooldown
@pytest.mark.parametrize("setup,path", [("BREAKOUT + ACCEPTANCE", path_no_pullback),
                                        ("SUPPORT BOUNCE", path_pullback)])
def test_one_signal_then_suppressed_while_active(setup, path):
    out = run(path, setup, 1)
    assert len(emitted(out)) == 1
    t_sig = emitted(out)[0][0]
    later = [d for t, d, _ in out if t_sig < t < t_sig + 5]
    assert later and all(d.signal is None for d in later)
    assert any(d.entry_state == SUPPRESSED and "already active" in d.entry_detail for d in later)


# --------------------------- 16: Telegram only after the final signal
class _Recorder:
    def __init__(self):
        self.signals, self.events = [], []

    def notify_signal(self, s):
        self.signals.append(s)
        return True

    def notify_event(self, e):
        self.events.append(e)
        return True


@pytest.mark.parametrize("sign", [1, -1])
def test_telegram_fires_once_on_the_pullback_fill_never_while_waiting(sign):
    cfg = load_config()
    tg = _Recorder()
    out = run(path_pullback, "MULTI-FACTOR LEVEL REACTION", sign)
    first_fill = next(t for t, d, _ in out if d.entry_state == PULLBACK_RECEIVED)
    for t, d, evs in out:
        run_engine.notify_new_signals(type("R", (), {"decisions": {"NIFTY": d}, "events": evs})(), tg)
        if t < first_fill:
            assert not tg.signals, "Telegram must never see an entry that is only waiting"
    issued = [d.signal for _, d in emitted(out)]
    assert tg.signals == issued, "Telegram receives exactly the authorized signals, nothing else"
    assert issued[0].direction == ("CALL" if sign > 0 else "PUT")
    assert cfg is not None


@pytest.mark.parametrize("sign", [1, -1])
def test_expired_entry_never_reaches_telegram(sign):
    tg = _Recorder()
    for t, d, evs in run(path_no_pullback, "FAILED BREAKOUT", sign):
        run_engine.notify_new_signals(type("R", (), {"decisions": {"NIFTY": d}, "events": evs})(), tg)
    assert tg.signals == []


# ------------------------------------------------ gates stay in force
def test_entry_cutoff_cancels_a_waiting_entry_explicitly():
    t0 = datetime(2026, 9, 24, 10, 0, tzinfo=IST)
    cutoff = t0 + timedelta(minutes=19)
    out = run(path_pullback, "SUPPORT BOUNCE", 1, entries_allowed=lambda ref: ref < cutoff)
    assert emitted(out) == []
    d = next(d for t, d, _ in out if 19.0 <= t < 19.4)
    assert any("pullback entry cancelled: new entries disabled" in r for r in d.reasons)
    assert d.entry_state == SIGNAL_GRADE_BLOCKED


def test_below_threshold_score_is_never_armed_or_emitted():
    out = run(path_pullback, "SUPPORT BOUNCE", 1, score=70.0)
    assert emitted(out) == [] and WAITING_FOR_PULLBACK not in states(out)
    assert SETUP_DETECTED in states(out)


@pytest.mark.parametrize("setup", ["SUPPORT BOUNCE", "BREAKOUT + ACCEPTANCE"])
def test_failed_risk_plan_is_reported_as_risk_rejected_never_armed(setup):
    out = run(path_pullback, setup, 1, risk_error="insufficient room: next level 5 pts away")
    assert emitted(out) == [] and WAITING_FOR_PULLBACK not in states(out)
    d = next(d for t, d, _ in out if t >= 18.0 and d.entry_state == RISK_REJECTED)
    assert "insufficient room" in d.entry_detail


def test_opposite_signal_cancels_the_waiting_entry():
    def flip(c, t):
        if t >= 18.7:
            return SetupCandidate("PUT", "BREAKDOWN + ACCEPTANCE", None, 23260, 23270, 0.8, "TEST", ["x"], None)
        return c
    out = run(path_pullback, "SUPPORT BOUNCE", 1, cand_hook=flip)
    d = next(d for _, d, _ in out if d.entry_state not in (WAITING_FOR_PULLBACK, NO_SETUP)
             and any("superseded" in r or "cancelled" in r for r in d.reasons))
    assert any("superseded by a PUT" in r for r in d.reasons)
    assert all(s.direction == "PUT" for _, s in [(t, d.signal) for t, d in emitted(out)])


def test_continuation_setup_supersedes_a_waiting_reversal_immediately():
    def switch(c, t):
        return SetupCandidate("CALL", "MOMENTUM CONTINUATION", None, 23205, 23197, 0.65, "TEST", ["x"], None) \
            if t >= 18.7 else c
    out = run(path_no_pullback, "SUPPORT BOUNCE", 1, cand_hook=switch)
    t, d = emitted(out)[0]
    assert 18.7 <= t < 19.1 and d.signal.setup == "MOMENTUM CONTINUATION"


# -------------------------------- every detected opportunity is explained
@pytest.mark.parametrize("path", [path_pullback, path_no_pullback, path_through_invalidation])
def test_every_detected_opportunity_has_an_explicit_entry_state(path):
    for setup in ("SUPPORT BOUNCE", "BREAKOUT + ACCEPTANCE"):
        for t, d, _ in run(path, setup, 1):
            if t >= 18.0 and d.status not in ("WARMING_UP", "MARKET_CLOSED", "DATA_GATE_BLOCKED"):
                assert d.entry_state != NO_SETUP, (t, d.status, d.reasons)


# ----------------------------------------------------- unit: burst check
T0 = datetime(2026, 9, 28, 14, 39, tzinfo=IST)


def _pipe():
    cfg = load_config()
    return IndexPipeline(cfg, "NIFTY", MarketClock(cfg), IntegrityGate(cfg), None)


def _bars(hl):
    return [Candle(T0 - timedelta(minutes=len(hl) - 1 - i), h, h, lo, lo, None, "T", complete=i < len(hl) - 1)
            for i, (h, lo) in enumerate(hl)]


def test_burst_measures_the_real_14_39_nifty_drop():
    b = _bars([(22785.65, 22782.7), (22783.5, 22782.15), (22782.15, 22770.05), (22765.6, 22763.9)])
    extreme, impulse = _pipe()._burst(-1, 22763.9, b, 5.0)
    assert extreme == 22785.65 and round(impulse, 2) == 21.75


def test_burst_is_direction_symmetric_and_needs_a_real_move():
    p, b = _pipe(), _bars([(100, 99), (101, 100), (102, 101), (103, 102)])
    assert p._burst(-1, 102.5, b, 5.0) is None
    assert p._burst(1, 112.0, b, 5.0) == (99, 13.0)
    assert p._burst(1, 104.0, b, 5.0) is None
    assert p._burst(1, 112.0, b, None) is None

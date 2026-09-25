"""End-to-end engine scenarios on real-schema simulated feeds."""

from datetime import datetime, timedelta

import pytest

from psygrid.config import load_config
from psygrid.market_clock import IST
from psygrid.monitor import Monitor
from psygrid.signal_engine import PsygridEngine

from sim import SimMarket, bull_breakout_path, chop_path


def run(sim: SimMarket, n: int):
    eng = PsygridEngine(load_config(), indices=("NIFTY",))
    out = []
    for _ in range(n):
        raws, now, S, phase = sim.step_raws()
        res = eng.cycle(raws, local_now=now)
        out.append((res, res.decisions["NIFTY"], phase))
    return eng, out


@pytest.fixture(scope="module")
def bull():
    return run(SimMarket(bull_breakout_path, sign=1), 120)


@pytest.fixture(scope="module")
def bear():
    return run(SimMarket(bull_breakout_path, sign=-1), 120)


def emitted(out):
    return [d.signal for _, d, _ in out if d.signal is not None]


def test_breakout_acceptance_emits_single_buy_call(bull):
    _, out = bull
    sigs = emitted(out)
    assert len(sigs) == 1
    s = sigs[0]
    assert s.direction == "CALL" and s.option_type == "CE" and s.setup == "BREAKOUT + ACCEPTANCE"
    assert s.score >= load_config()["scoring"]["signal_threshold"]
    # every required output field is present
    for f in ("index", "strike", "underlying", "option_ltp", "key_level_price", "level_type", "entry_low",
              "entry_high", "invalidation", "t1", "t2", "confirmations", "created"):
        assert getattr(s, f) is not None
    assert s.invalidation < s.underlying < s.t1 < s.t2
    assert s.entry_low <= s.option_ltp <= s.entry_high


def test_engine_waits_for_acceptance_before_signal(bull):
    _, out = bull
    signal_i = next(i for i, (_, d, _) in enumerate(out) if d.signal)
    waits = [i for i, (_, d, _) in enumerate(out[:signal_i])
             if any("WAIT FOR ACCEPTANCE" in w for w in d.waiting)]
    assert waits, "engine never waited for acceptance after the breakout"
    # while waiting, nothing was emitted
    assert all(out[i][1].signal is None for i in waits)


def test_mirror_scenario_emits_buy_put_with_same_quality(bull, bear):
    b, p = emitted(bull[1])[0], emitted(bear[1])[0]
    assert p.direction == "PUT" and p.option_type == "PE" and p.setup == "BREAKDOWN + ACCEPTANCE"
    assert p.created == b.created
    assert p.score == pytest.approx(b.score, abs=0.5)
    assert p.strike == b.strike and p.option_ltp == pytest.approx(b.option_ltp)
    assert (b.t1 - b.underlying) == pytest.approx(p.underlying - p.t1, abs=0.01)


@pytest.mark.parametrize("fixture_name,direction,option_type", [("bull", "CALL", "CE"), ("bear", "PUT", "PE")])
def test_positive_path_passes_every_named_stage_before_authorization(fixture_name, direction, option_type,
                                                                      request):
    """Explicit stage-by-stage proof (not just the final Signal) that a
    realistic opportunity genuinely reaches: setup detected -> confirmation
    generated -> score -> risk -> BUY CALL/PUT, through the unmodified
    production path, for BOTH directions."""
    _, out = request.getfixturevalue(fixture_name)
    signal_i = next(i for i, (_, d, _) in enumerate(out) if d.signal)
    d = out[signal_i][1]

    assert d.trace is not None and d.trace.setup_detected             # setup detected
    assert d.trace.direction == direction
    assert len(d.trace.passing) >= d.trace.confirmations_required     # confirmation generated
    assert not d.trace.conflicts
    assert d.trace.score >= d.trace.signal_threshold                  # score
    assert d.trace.grade == "SIGNAL"
    assert d.trace.risk_pass                                          # risk
    assert d.best is not None and d.best.plan is not None
    assert d.status == f"BUY_{direction}"                             # authorized
    assert d.signal is not None and d.signal.option_type == option_type


def test_lifecycle_suppression_is_rendered_not_silent(bull):
    """Pre-scoring starvation audit, live-observability requirement F:
    once a signal is active, the setup engine keeps re-detecting the same
    zone's ACCEPTED event each cycle (it's still within max_event_age) and
    the candidate still scores SIGNAL-grade - state.consider() correctly
    suppresses it as a duplicate ("already active"), but the terminal must
    say so, not render a trace that looks identical to "nothing found"."""
    _, out = bull
    signal_i = next(i for i, (_, d, _) in enumerate(out) if d.signal)
    suppressed = [(r, d) for r, d, _ in out[signal_i + 1:]
                 if d.status == "SIGNAL_ACTIVE" and d.signal is None
                 and d.trace and d.trace.grade == "SIGNAL"]
    assert suppressed, "scenario never re-detected the same setup after the signal - test would prove nothing"
    res, d = suppressed[0]
    assert any("already active" in r for r in d.reasons)
    text = Monitor(color=False, ascii_only=True).render(res, [])
    assert "SUPPRESSED:" in text and "already active" in text


def test_target_event_after_signal(bull):
    eng, out = bull
    events = [e.event for res, _, _ in out for e in res.events]
    assert "SIGNAL" in events and "TARGET_1" in events


def test_terminal_render_contains_signal_fields(bull):
    _, out = bull
    res = next(r for r, d, _ in out if d.signal)
    text = Monitor(color=False, ascii_only=True).render(res, [])
    for needle in (">>> BUY CALL <<<", "Strike", "Option LTP", "Underlying", "SETUP", "KEY LEVEL",
                   "LEVEL TYPE", "Entry", "Invalidation", "Target 1", "Target 2", "QUALITY", "CONFIRMATION"):
        assert needle in text


def test_terminal_render_shows_confirmation_trace_before_signal(bull):
    """Audit Phase 10: a repeated NO_TRADE/WATCH before the eventual BUY
    CALL must be diagnosable (which confirmations passed/are missing, how
    far the score is from threshold), not just a bare status string."""
    _, out = bull
    signal_i = next(i for i, (_, d, _) in enumerate(out) if d.signal)
    traced = [d for _, d, _ in out[:signal_i] if d.trace and d.trace.setup_detected]
    assert traced, "no diagnosable candidate before the eventual signal - test would prove nothing"
    res = next(r for r, d, _ in out[:signal_i] if d.trace and d.trace.setup_detected)
    text = Monitor(color=False, ascii_only=True).render(res, [])
    assert "Confirmations:" in text
    assert "PASS:" in text or "MISSING:" in text


def test_diagnostic_mode_shows_full_per_confirmation_breakdown(bull):
    _, out = bull
    signal_i = next(i for i, (_, d, _) in enumerate(out) if d.signal)
    res = next(r for r, d, _ in out[:signal_i] if d.trace and d.trace.setup_detected)
    text = Monitor(color=False, ascii_only=True, diagnostic=True).render(res, [])
    for label in ("Futures confirmation", "Option participation", "Depth confirmation",
                  "Volume / participation expansion", "VWAP / indicators"):
        assert label in text


def test_chop_with_unavailable_confirmations_is_no_trade():
    _, out = run(SimMarket(chop_path, futures_ok=False, indicators_ok=False, flows=False), 90)
    assert not emitted(out)
    statuses = {d.status for _, d, _ in out}
    assert statuses <= {"WARMING_UP", "NO_TRADE", "WATCH"}


def test_bullish_depth_alone_never_buys():
    sim = SimMarket(chop_path, futures_ok=False, indicators_ok=False, flow_map={},
                    depth_flow_map={"chop": 1})
    _, out = run(sim, 90)
    assert not emitted(out)


def test_stale_feed_blocks():
    sim = SimMarket(bull_breakout_path)
    eng = PsygridEngine(load_config(), indices=("NIFTY",))
    raws, now, _, _ = sim.step_raws()
    res = eng.cycle(raws, local_now=now + timedelta(minutes=3))
    d = res.decisions["NIFTY"]
    assert d.status == "DATA_GATE_BLOCKED" and any("stale" in r for r in d.reasons)


def test_market_closed_before_open():
    sim = SimMarket(bull_breakout_path, start=datetime(2026, 9, 24, 8, 30, tzinfo=IST))
    _, out = run(sim, 2)
    assert all(d.status == "MARKET_CLOSED" for _, d, _ in out)


def test_weekend_closed():
    sim = SimMarket(bull_breakout_path, start=datetime(2026, 9, 26, 11, 0, tzinfo=IST))
    _, out = run(sim, 1)
    assert out[0][1].status == "MARKET_CLOSED"


def test_no_new_entries_late_session():
    sim = SimMarket(bull_breakout_path, start=datetime(2026, 9, 24, 14, 40, tzinfo=IST))
    _, out = run(sim, 100)
    assert not emitted(out)
    late = [d for r, d, _ in out if r.ref_time.hour == 15 and d.status not in ("WARMING_UP",)]
    assert late and all("new entries disabled" in " ".join(d.reasons) or d.status == "MARKET_CLOSED"
                        for d in late)


def test_late_session_setup_is_still_traced_not_silently_dropped():
    """Pre-scoring starvation audit: a SIGNAL-grade candidate detected
    during the 15:00-15:20 entry-cutoff window must still be scored and
    traced (IndexDecision.trace) even though it can never be authorized -
    otherwise "found but intentionally rejected" is indistinguishable from
    "never found" (see docs/SIGNAL_PIPELINE_AUDIT.md). The suppression
    itself must be unaffected: status/signal must never become BUY_*."""
    sim = SimMarket(bull_breakout_path, start=datetime(2026, 9, 24, 14, 40, tzinfo=IST))
    _, out = run(sim, 70)
    assert not emitted(out)  # entry cutoff must still hold - nothing authorized

    traced_signal_grade = [d for _, d, _ in out
                           if d.trace and d.trace.setup_detected and d.trace.grade == "SIGNAL"]
    assert traced_signal_grade, ("scenario never produced a SIGNAL-grade candidate during the cutoff "
                                 "window - test would prove nothing")
    for d in traced_signal_grade:
        assert d.status in ("NO_TRADE", "SIGNAL_ACTIVE")   # correctly suppressed, not authorized
        assert d.trace.direction == "CALL" and d.trace.setup == "BREAKOUT + ACCEPTANCE"
        assert any("new entries disabled" in r for r in d.reasons)


def test_futures_unavailable_lowers_quality():
    _, out_ok = run(SimMarket(bull_breakout_path), 70)
    _, out_nf = run(SimMarket(bull_breakout_path, futures_ok=False), 70)
    q_ok = [d.best.score.score for _, d, _ in out_ok if d.best]
    q_nf = [d.best.score.score for _, d, _ in out_nf if d.best]
    assert q_ok and q_nf and max(q_nf) < max(q_ok)

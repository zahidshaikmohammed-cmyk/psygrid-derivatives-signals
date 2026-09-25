"""Unit tests for diagnostics.py's SignalEvaluationTrace (audit Phase 4).

These construct ScoreResult/GateResult by hand so each branch of
build_trace() can be tested independently of the full pipeline (the
pipeline-level proof that traces populate correctly during a real
simulated setup lives in test_scenarios.py / test_engine_io.py).
"""

from datetime import datetime

from psygrid.config import load_config
from psygrid.data_integrity import GateResult
from psygrid.diagnostics import build_trace
from psygrid.market_clock import IST
from psygrid.models import FeedCheck
from psygrid.scoring_engine import Component, ScoreResult
from psygrid.setup_engine import SetupCandidate

CFG = load_config()
NOW = datetime(2026, 9, 24, 11, 0, tzinfo=IST)


def cand(direction="CALL", setup="BREAKOUT + ACCEPTANCE") -> SetupCandidate:
    return SetupCandidate(direction=direction, setup=setup, key_zone=None, level_price=23200.0,
                          invalidation=23150.0, quality=0.8, market_state="ACCEPTANCE ABOVE LEVEL")


def comps(**overrides) -> dict[str, Component]:
    base = {
        "structure": Component("structure", 0.5, "trend UP"),
        "level": Component("level", 0.7, "level"),
        "futures": Component("futures", None, "futures feed unavailable"),
        "momentum": Component("momentum", 0.5, "momentum"),
        "volume": Component("volume", None, "building baseline"),
        "options": Component("options", None, "building option-flow history"),
        "liquidity": Component("liquidity", 0.5, "liquidity"),
        "depth": Component("depth", None, "depth unavailable"),
        "vwap_indicators": Component("vwap_indicators", 0.6, "price above VWAP"),
        "setup": Component("setup", 0.8, "setup"),
        "data_quality": Component("data_quality", 0.9, "0.90"),
    }
    base.update(overrides)
    return base


def score(grade="NO_TRADE", value=50.0, confirmations=(), conflicts=(), reasons=()) -> ScoreResult:
    return ScoreResult(value, grade, comps(), list(confirmations), list(conflicts), list(reasons))


def gate(**feed_overrides) -> GateResult:
    feeds = {
        "spot": FeedCheck("spot", "OK"),
        "options": FeedCheck("options", "OK"),
        "depth": FeedCheck("depth", "BLOCKED", reasons=["status=ERROR (websocket dropped)"]),
        "futures": FeedCheck("futures", "BLOCKED", reasons=["status=ERROR (contract unresolved)"]),
        "indicators": FeedCheck("indicators", "OK"),
    }
    feeds.update(feed_overrides)
    return GateResult(index="NIFTY", authorization="AUTHORIZED", reasons=[], notes=[], feeds=feeds,
                      underlying_price=23200.0, data_quality=0.9)


def test_no_candidate_means_setup_not_detected():
    t = build_trace("NIFTY", None, None, gate(), CFG)
    assert t.setup_detected is False
    assert t.final_decision == "NO_TRADE"
    assert t.rejection_reason == "no setup candidate this cycle"


def test_confirmations_split_into_passing_and_missing():
    sc = score(confirmations=["futures", "vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG)
    assert t.setup_detected is True
    assert t.direction == "CALL" and t.setup == "BREAKOUT + ACCEPTANCE"
    assert set(t.passing) == {"Futures confirmation", "VWAP / indicators"}
    assert set(t.missing) == {"Option participation", "Depth confirmation", "Volume / participation expansion"}
    # every INDEPENDENT key has exactly one ConfirmationCheck
    assert {c.key for c in t.confirmations} == {"futures", "options", "depth", "volume", "vwap_indicators"}
    assert next(c for c in t.confirmations if c.key == "futures").passed is True
    assert next(c for c in t.confirmations if c.key == "depth").passed is False


def test_blocking_explains_unavailable_confirmation_from_gate_feed_state():
    sc = score(confirmations=["vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG)
    joined = "; ".join(t.blocking)
    assert "depth blocked" in joined and "websocket dropped" in joined
    assert "futures blocked" in joined and "contract unresolved" in joined


def test_blocking_falls_back_to_component_detail_when_no_owning_feed():
    # "volume" and "options" have no single owning feed in _FEED_FOR - they
    # must explain themselves from the component's own detail text.
    sc = score(confirmations=["futures", "vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(options=FeedCheck("options", "OK")), CFG)
    joined = "; ".join(t.blocking)
    assert "building option-flow history" in joined or "building baseline" in joined


def test_near_miss_only_when_confirmation_and_conflict_gates_already_pass():
    req = CFG["scoring"]["min_independent_confirmations"]
    assert req == 2, "test assumes the default config's confirmation requirement"
    thr = CFG["scoring"]["signal_threshold"]

    # gates satisfied (2 confirmations), score is the sole remaining blocker
    sc = score(grade="NO_TRADE", value=thr - 5, confirmations=["futures", "vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG)
    assert t.near_miss_points == 5.0

    # confirmations short of the requirement: score gap is NOT the story,
    # so near_miss must stay unset even though the number would be positive
    sc2 = score(grade="NO_TRADE", value=thr - 5, confirmations=["futures"])
    t2 = build_trace("NIFTY", cand(), sc2, gate(), CFG)
    assert t2.near_miss_points is None


def test_signal_grade_has_no_near_miss():
    sc = score(grade="SIGNAL", value=90.0, confirmations=["futures", "vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG)
    assert t.near_miss_points is None
    assert t.grade == "SIGNAL"


def test_conflicts_are_labelled():
    sc = score(conflicts=["momentum", "structure"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG)
    assert set(t.conflicts) == {"Momentum", "Underlying structure"}


def test_risk_pass_false_when_signal_grade_but_plan_rejected():
    sc = score(grade="SIGNAL", value=90.0, confirmations=["futures", "vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG,
                    plan_error="insufficient room: next level 23260.0 is 10.0 pts away")
    assert t.risk_pass is False
    assert "insufficient room" in t.risk_reason


def test_risk_pass_true_when_no_plan_error():
    sc = score(grade="SIGNAL", value=90.0, confirmations=["futures", "vwap_indicators"])
    t = build_trace("NIFTY", cand(), sc, gate(), CFG, plan_error="")
    assert t.risk_pass is True and t.risk_reason is None


def test_risk_pass_true_when_grade_is_not_signal_even_with_plan_error():
    # plan_error is only meaningful once the score/confirmation gates
    # already said SIGNAL - it must not be reported as the blocker for a
    # candidate that was already rejected earlier in the pipeline.
    sc = score(grade="NO_TRADE", value=50.0)
    t = build_trace("NIFTY", cand(), sc, gate(), CFG, plan_error="no eligible contract")
    assert t.risk_pass is True and t.risk_reason is None

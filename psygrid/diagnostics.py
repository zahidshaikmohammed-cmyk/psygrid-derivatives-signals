"""Signal-rejection diagnostics: "why didn't I get a signal?" (audit Phase 4).

This module is read-only and strictly downstream of the real decision:
it is built AFTER `ScoringEngine.score()` has already produced its
`ScoreResult`, and it never feeds back into confirmation counting, the
score itself, risk validation, or `SignalStateManager`. Nothing here can
loosen or bypass the production authorization boundary in
`IndexPipeline.run()` (signal_engine.py) - it only explains, in
structured/machine-readable form, why the score/confirmation layer
reached the decision it reached for the best candidate this cycle, so
`monitor.py` (and any future tooling) can answer "why no signal?" with
more than a single truncated reason string.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .data_integrity import GateResult
from .scoring_engine import INDEPENDENT, LABELS, ScoreResult
from .setup_engine import SetupCandidate

# Which upstream feed (data_integrity.py's feed names) each INDEPENDENT
# confirmation ultimately depends on, when that mapping is direct enough
# to explain a None value from a feed's own BLOCKED/DEGRADED reasons.
# "volume" and "vwap_indicators" have no single owning feed (they can come
# from options activity OR indicators OR raw VWAP), so they are left out
# and explained from the component's own detail text instead.
_FEED_FOR = {"futures": "futures", "options": "options", "depth": "depth"}


@dataclass(frozen=True)
class ConfirmationCheck:
    key: str
    label: str
    value: Optional[float]     # -1..1, direction-relative; None = unavailable
    passed: bool
    detail: str


@dataclass(frozen=True)
class SignalEvaluationTrace:
    """One index's evaluation of its best candidate this cycle. ``None``
    fields mean "no candidate was evaluated" (``setup_detected=False``)."""

    index: str
    setup_detected: bool
    direction: Optional[str] = None
    setup: Optional[str] = None
    score: Optional[float] = None
    grade: Optional[str] = None                    # SIGNAL | WATCH | NO_TRADE
    signal_threshold: Optional[float] = None
    watch_threshold: Optional[float] = None
    confirmations_required: Optional[int] = None
    confirmations: list[ConfirmationCheck] = field(default_factory=list)
    passing: list[str] = field(default_factory=list)      # confirmation labels that passed
    missing: list[str] = field(default_factory=list)      # confirmation labels that didn't
    blocking: list[str] = field(default_factory=list)     # WHY a missing one is unavailable
    conflicts: list[str] = field(default_factory=list)    # directional components strongly opposed
    final_decision: str = "NO_TRADE"
    rejection_reason: Optional[str] = None
    near_miss_points: Optional[float] = None       # set only when score is the sole remaining blocker
    risk_pass: bool = True
    risk_reason: Optional[str] = None


def build_trace(index: str, cand: Optional[SetupCandidate], score: Optional[ScoreResult],
                 gate: GateResult, cfg, *, plan_error: str = "") -> SignalEvaluationTrace:
    if cand is None or score is None:
        return SignalEvaluationTrace(index=index, setup_detected=False, final_decision="NO_TRADE",
                                     rejection_reason="no setup candidate this cycle")
    sc = cfg["scoring"]
    checks: list[ConfirmationCheck] = []
    passing: list[str] = []
    missing: list[str] = []
    blocking: list[str] = []
    for k in INDEPENDENT:
        c = score.components.get(k)
        val = c.value if c else None
        passed = k in score.confirmations
        checks.append(ConfirmationCheck(k, LABELS[k], val, passed, c.detail if c else "n/a"))
        (passing if passed else missing).append(LABELS[k])
        if passed or val is not None:
            continue
        feed = _FEED_FOR.get(k)
        fc = gate.feeds.get(feed) if feed else None
        if fc is not None and not fc.usable:
            blocking.append(f"{feed} {fc.state.lower()}" + (f": {'; '.join(fc.reasons)}" if fc.reasons else ""))
        else:
            blocking.append(f"{LABELS[k]}: {(c.detail if c else 'unavailable')}"[:100])

    near_miss = None
    if (score.grade != "SIGNAL" and len(score.conflicts) <= sc["max_strong_conflicts"]
            and len(score.confirmations) >= sc["min_independent_confirmations"]):
        gap = sc["signal_threshold"] - score.score
        if gap > 0:
            near_miss = round(gap, 1)

    risk_pass = not (score.grade == "SIGNAL" and plan_error)
    return SignalEvaluationTrace(
        index=index, setup_detected=True, direction=cand.direction, setup=cand.setup,
        score=score.score, grade=score.grade, signal_threshold=sc["signal_threshold"],
        watch_threshold=sc["watch_threshold"], confirmations_required=sc["min_independent_confirmations"],
        confirmations=checks, passing=passing, missing=missing, blocking=blocking,
        conflicts=[LABELS[k] for k in score.conflicts], final_decision=score.grade,
        rejection_reason=(score.reasons[0] if score.reasons else None), near_miss_points=near_miss,
        risk_pass=risk_pass, risk_reason=(plan_error or None) if not risk_pass else None,
    )

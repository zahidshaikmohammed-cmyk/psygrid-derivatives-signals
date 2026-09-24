"""Virtual signal state + deduplication (no orders are ever placed).

States: FLAT -> SIGNAL_ACTIVE -> TARGET_1 -> TARGET_2 -> CLOSED
                              -> INVALIDATED -> CLOSED
A signal is also CLOSED by its time stop, by an opposing high-quality signal
or at the configured session close. After TARGET_1 the virtual stop (``stop``)
moves to the underlying entry price; the emitted ``invalidation`` never changes (documented behaviour of this model).

Deduplication: while a signal is active for an index, same-direction
candidates are suppressed. After a signal closes, the identical signal key
(direction, strike, type, setup, key level) is suppressed for the cooldown
period, and so is any same-direction signal after an invalidation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .config import Config


@dataclass
class Signal:
    id: str
    index: str
    direction: str
    strike: float
    option_type: str
    setup: str
    key_level_id: Optional[str]
    key_level_price: float
    level_type: str
    level_strength: Optional[float]
    market_state: str
    underlying: float
    underlying_source: str
    option_ltp: float
    bid: float
    ask: float
    spread_pct: float
    entry_low: float
    entry_high: float
    invalidation: float
    t1: float
    t2: float
    option_invalidation: Optional[float]
    option_t1: Optional[float]
    option_t2: Optional[float]
    reward_risk: float
    target_basis: str
    holding: str
    max_hold_minutes: int
    score: float
    grade: str
    confirmations: list[tuple[str, str, str]]     # (label, mark, detail)
    evidence: list[str]
    strike_reasons: list[str]
    notes: list[str]
    created: datetime
    state: str = "SIGNAL_ACTIVE"
    state_ts: Optional[datetime] = None
    history: list[tuple[datetime, str, str]] = field(default_factory=list)
    stop: Optional[float] = None      # current virtual stop; starts at the emitted invalidation

    def __post_init__(self):
        if self.stop is None:
            self.stop = self.invalidation

    @property
    def key(self) -> tuple:
        return (self.direction, self.strike, self.option_type, self.setup, self.key_level_id)

    @property
    def sign(self) -> int:
        return 1 if self.direction == "CALL" else -1


@dataclass
class SignalEvent:
    ts: datetime
    index: str
    event: str
    text: str
    signal_id: Optional[str] = None


class SignalStateManager:
    def __init__(self, cfg: Config):
        self.c = cfg["signal_state"]
        self.active: dict[str, Signal] = {}
        self.closed: dict[str, list[Signal]] = {}
        self._seq = 0

    def new_id(self, index: str, now: datetime) -> str:
        self._seq += 1
        return f"{index}-{now:%Y%m%d-%H%M%S}-{self._seq}"

    def state_of(self, index: str) -> str:
        s = self.active.get(index)
        return s.state if s else "FLAT"

    # ---------------------------------------------------------------- tracking
    def _transition(self, s: Signal, state: str, now: datetime, note: str, events: list) -> None:
        s.state, s.state_ts = state, now
        s.history.append((now, state, note))
        events.append(SignalEvent(now, s.index, state,
                                  f"{s.index} {s.direction} {s.strike:,.0f} {s.option_type}: {state} — {note}", s.id))

    def _close(self, s: Signal, now: datetime, note: str, events: list) -> None:
        self._transition(s, "CLOSED", now, note, events)
        self.closed.setdefault(s.index, []).append(s)
        self.active.pop(s.index, None)

    def track(self, index: str, price: Optional[float], now: datetime, session_closing: bool) -> list[SignalEvent]:
        s = self.active.get(index)
        events: list[SignalEvent] = []
        if s is None:
            return events
        if session_closing:
            self._close(s, now, "session close", events)
            return events
        if price is None:
            return events
        d = s.sign
        if (price - s.stop) * d <= 0:
            self._transition(s, "INVALIDATED", now, f"underlying {price:,.2f} through {s.stop:,.2f}", events)
            self._close(s, now, "invalidated", events)
            return events
        if s.state == "SIGNAL_ACTIVE" and (price - s.t1) * d >= 0:
            self._transition(s, "TARGET_1", now, f"underlying {price:,.2f} reached T1 {s.t1:,.2f}; "
                             f"virtual stop -> entry {s.underlying:,.2f}", events)
            s.stop = s.underlying
        if s.state == "TARGET_1" and (price - s.t2) * d >= 0:
            self._transition(s, "TARGET_2", now, f"underlying {price:,.2f} reached T2 {s.t2:,.2f}", events)
            self._close(s, now, "final target reached", events)
            return events
        if now - s.created >= timedelta(minutes=s.max_hold_minutes):
            self._close(s, now, f"time stop ({s.max_hold_minutes} min)", events)
        return events

    # ----------------------------------------------------------- deduplication
    def consider(self, sig: Signal, now: datetime) -> tuple[bool, str, list[SignalEvent]]:
        events: list[SignalEvent] = []
        act = self.active.get(sig.index)
        if act is not None:
            if act.direction == sig.direction:
                return False, f"{act.direction} signal already active ({act.state}) — not repeated", events
            self._close(act, now, f"opposing {sig.direction} signal ({sig.setup})", events)
        cooldown = timedelta(seconds=self.c["cooldown_seconds"])
        for old in reversed(self.closed.get(sig.index, [])):
            if now - (old.state_ts or old.created) > cooldown:
                break
            if old.key == sig.key and not (sig.score - old.score >= self.c["requalify_score_jump"]):
                return False, "identical signal recently closed — cooldown", events
            if old.direction == sig.direction and any(h[1] == "INVALIDATED" for h in old.history):
                return False, f"cooldown after invalidated {old.direction}", events
        self.active[sig.index] = sig
        sig.state_ts = now
        sig.history.append((now, "SIGNAL_ACTIVE", "emitted"))
        events.append(SignalEvent(now, sig.index, "SIGNAL",
                                  f"{sig.index} BUY {sig.direction} {sig.strike:,.0f} {sig.option_type} "
                                  f"@ {sig.option_ltp:.2f} ({sig.setup}, Q{sig.score:.0f})", sig.id))
        return True, "emitted", events

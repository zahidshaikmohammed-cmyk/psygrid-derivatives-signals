"""Telegram notifications for a newly-accepted signal (read-only side channel).

This module is deliberately isolated from the decision engine: nothing in
``signal_engine.py`` or ``signal_state.py`` imports it, and it never raises.
Every public method catches its own errors and returns a bool instead, so a
Telegram outage, a bad token, or missing configuration can only ever
degrade to "no notification sent" - it can never block, delay, or crash a
poll cycle (this engine places no orders; see run_engine.py's own
docstring - notification failures matter even less here than in a live
trading system, but the isolation is enforced anyway).

Enabled only when both PSYGRID_TELEGRAM_BOT_TOKEN and
PSYGRID_TELEGRAM_CHAT_ID are set as environment variables - no secret is
ever read from config.json or hardcoded.

Wired in from run_engine.py at the same point ``IndexDecision.signal`` is
populated: that field is only set inside ``IndexPipeline.run()`` after
``SignalStateManager.consider()`` returns ``ok=True`` for the cycle - i.e.
a signal that just passed dedup/cooldown and was newly registered as the
index's active signal, not a repeat, not a candidate still forming. That
existing guard is this module's entire dedup story; nothing here needs to
re-implement it.
"""

from __future__ import annotations

import os
import sys
from typing import Callable, Optional

import requests

from .signal_state import Signal

_TELEGRAM_API_BASE = "https://api.telegram.org"
_REQUEST_TIMEOUT_SECONDS = 10.0

_TOKEN_ENV = "PSYGRID_TELEGRAM_BOT_TOKEN"
_CHAT_ID_ENV = "PSYGRID_TELEGRAM_CHAT_ID"


class TelegramNotifier:
    """``poster`` is injectable for tests (mirrors ``DataClient``'s
    ``getter`` param) - defaults to ``requests.post``."""

    def __init__(self, poster: Optional[Callable] = None) -> None:
        self._token = os.environ.get(_TOKEN_ENV) or None
        self._chat_id = os.environ.get(_CHAT_ID_ENV) or None
        self._post = poster or requests.post

    @property
    def enabled(self) -> bool:
        return bool(self._token) and bool(self._chat_id)

    def _send(self, text: str) -> bool:
        if not self.enabled:
            return False
        url = f"{_TELEGRAM_API_BASE}/bot{self._token}/sendMessage"
        try:
            resp = self._post(url, json={"chat_id": self._chat_id, "text": text},
                              timeout=_REQUEST_TIMEOUT_SECONDS)
            if getattr(resp, "status_code", 500) >= 400:
                print(f"[telegram] notification failed: HTTP {resp.status_code}", file=sys.stderr)
                return False
            return True
        except requests.RequestException as exc:
            print(f"[telegram] notification failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return False
        except Exception as exc:  # never let a notification failure reach the caller
            print(f"[telegram] notification failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return False

    def notify_signal(self, sig: Signal) -> bool:
        lines = [
            f"{sig.index} BUY {sig.direction} {sig.strike:,.0f} {sig.option_type} "
            f"({sig.setup}, Q{sig.score:.0f} {sig.grade})",
            f"Option LTP: {sig.option_ltp:.2f}  Entry: {sig.entry_low:.2f}-{sig.entry_high:.2f}",
            f"Invalidation: {sig.invalidation:,.2f}  T1: {sig.t1:,.2f}  T2: {sig.t2:,.2f}  "
            f"R:R: {sig.reward_risk:.2f}",
            f"Underlying: {sig.underlying:,.2f} ({sig.underlying_source})  "
            f"Level: {sig.level_type} @ {sig.key_level_price:,.2f}",
            "Signal-only - no order has been placed.",
        ]
        return self._send("\n".join(lines))

    def send_test_message(self) -> bool:
        return self._send("PSYGRID Options Engine: Telegram notifications are configured correctly.")

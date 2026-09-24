"""IST market clock and session phases. No dates are hard-coded."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from .config import Config

IST = timezone(timedelta(hours=5, minutes=30), name="IST")

PRE_OPEN = "MARKET CLOSED (PRE-OPEN)"
OPEN = "OPEN"
LATE = "OPEN (NO NEW ENTRIES)"
CLOSING = "CLOSING (SIGNALS BEING CLOSED)"
CLOSED = "MARKET CLOSED"
WEEKEND = "MARKET CLOSED (WEEKEND)"


def now_ist() -> datetime:
    return datetime.now(IST)


def _t(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


class MarketClock:
    def __init__(self, cfg: Config):
        s = cfg["session"]
        self.open = _t(s["open"])
        self.close = _t(s["close"])
        self.no_new = _t(s["no_new_entries_after"])
        self.close_signals = _t(s["close_signals_at"])
        self.or_minutes = int(s["opening_range_minutes"])
        self.weekdays_only = bool(s["weekdays_only"])

    def phase(self, now: datetime) -> str:
        now = now.astimezone(IST)
        if self.weekdays_only and now.weekday() >= 5:
            return WEEKEND
        t = now.time()
        if t < self.open:
            return PRE_OPEN
        if t >= self.close:
            return CLOSED
        if t >= self.close_signals:
            return CLOSING
        if t >= self.no_new:
            return LATE
        return OPEN

    def entries_allowed(self, now: datetime) -> bool:
        return self.phase(now) == OPEN

    def is_session(self, now: datetime) -> bool:
        return self.phase(now) in (OPEN, LATE, CLOSING)

    def session_open_dt(self, now: datetime) -> datetime:
        now = now.astimezone(IST)
        return datetime.combine(now.date(), self.open, tzinfo=IST)

    def opening_range_end(self, now: datetime) -> datetime:
        return self.session_open_dt(now) + timedelta(minutes=self.or_minutes)

    def minutes_to_close(self, now: datetime) -> float:
        end = datetime.combine(now.astimezone(IST).date(), self.close, tzinfo=IST)
        return (end - now).total_seconds() / 60

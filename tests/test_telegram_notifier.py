from datetime import datetime

import pytest

from psygrid.market_clock import IST
from psygrid.telegram_notifier import TelegramNotifier

from test_signal_state import sig

T0 = datetime(2026, 9, 24, 11, 0, tzinfo=IST)


class FakeResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code


def _fake_poster(calls, status_code=200):
    def poster(url, json=None, timeout=None):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse(status_code)
    return poster


def _raising_poster(exc):
    def poster(url, json=None, timeout=None):
        raise exc
    return poster


@pytest.fixture(autouse=True)
def _clear_telegram_env(monkeypatch):
    monkeypatch.delenv("PSYGRID_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("PSYGRID_TELEGRAM_CHAT_ID", raising=False)


def _enabled_notifier(monkeypatch, poster):
    monkeypatch.setenv("PSYGRID_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PSYGRID_TELEGRAM_CHAT_ID", "12345")
    return TelegramNotifier(poster=poster)


def test_disabled_without_credentials_never_calls_network():
    calls = []
    notifier = TelegramNotifier(poster=_fake_poster(calls))
    assert notifier.enabled is False
    assert notifier.notify_signal(sig()) is False
    assert notifier.send_test_message() is False
    assert calls == []


@pytest.mark.parametrize("missing", ["PSYGRID_TELEGRAM_BOT_TOKEN", "PSYGRID_TELEGRAM_CHAT_ID"])
def test_disabled_when_only_one_credential_set(monkeypatch, missing):
    monkeypatch.setenv("PSYGRID_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PSYGRID_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.delenv(missing, raising=False)
    notifier = TelegramNotifier(poster=_fake_poster([]))
    assert notifier.enabled is False


def test_enabled_when_both_credentials_set(monkeypatch):
    notifier = _enabled_notifier(monkeypatch, _fake_poster([]))
    assert notifier.enabled is True


def test_notify_signal_posts_expected_payload(monkeypatch):
    calls = []
    notifier = _enabled_notifier(monkeypatch, _fake_poster(calls))

    ok = notifier.notify_signal(sig())

    assert ok is True
    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == "https://api.telegram.org/bottest-token/sendMessage"
    assert call["json"]["chat_id"] == "12345"
    text = call["json"]["text"]
    assert "NIFTY BUY CALL" in text
    assert "23,200" in text
    assert "Signal-only" in text


def test_notify_signal_put_direction(monkeypatch):
    calls = []
    notifier = _enabled_notifier(monkeypatch, _fake_poster(calls))
    ok = notifier.notify_signal(sig("PUT"))
    assert ok is True
    assert "BUY PUT" in calls[0]["json"]["text"]


def test_send_test_message_posts_confirmation_text(monkeypatch):
    calls = []
    notifier = _enabled_notifier(monkeypatch, _fake_poster(calls))
    assert notifier.send_test_message() is True
    assert "configured correctly" in calls[0]["json"]["text"]


def test_http_error_status_never_raises_and_returns_false(monkeypatch):
    notifier = _enabled_notifier(monkeypatch, _fake_poster([], status_code=401))
    assert notifier.notify_signal(sig()) is False


def test_network_exception_never_raises_and_returns_false(monkeypatch):
    import requests
    notifier = _enabled_notifier(monkeypatch, _raising_poster(requests.ConnectionError("refused")))
    assert notifier.notify_signal(sig()) is False


def test_unexpected_poster_exception_never_raises_and_returns_false(monkeypatch):
    notifier = _enabled_notifier(monkeypatch, _raising_poster(RuntimeError("boom")))
    assert notifier.notify_signal(sig()) is False


def _events_for_time_stop(ltp):
    from datetime import timedelta
    from psygrid.config import load_config
    from psygrid.signal_state import SignalStateManager
    m = SignalStateManager(load_config())
    m.consider(sig("PUT", strike=22800.0), T0)
    return m.track("NIFTY", 23225, T0 + timedelta(minutes=41), False, option_ltp=lambda s: ltp)


def test_notify_event_time_stop_with_pnl(monkeypatch):
    calls = []
    n = _enabled_notifier(monkeypatch, _fake_poster(calls))
    ev = _events_for_time_stop(92.0)[-1]
    assert n.notify_event(ev) is True
    text = calls[0]["json"]["text"]
    assert text.startswith("NIFTY PUT 22,800 PE - CLOSED: time stop (40 min)")
    assert "Option LTP: 92.00 (signal 100.00)  P&L: -8.00 pts (-8.0%)" in text
    assert "Underlying: 23,225.00" in text and "no order has been placed" in text


def test_notify_event_target1_and_skips_other_kinds(monkeypatch):
    from datetime import timedelta
    from psygrid.config import load_config
    from psygrid.signal_state import SignalStateManager
    calls = []
    n = _enabled_notifier(monkeypatch, _fake_poster(calls))
    m = SignalStateManager(load_config())
    _, _, emitted = m.consider(sig(), T0)
    assert n.notify_event(emitted[0]) is False  # the new signal itself goes via notify_signal
    ev = m.track("NIFTY", 23262, T0 + timedelta(minutes=2), False, option_ltp=lambda s: 120.0)
    assert n.notify_event(ev[0]) is True
    assert "TARGET 1 HIT" in calls[-1]["json"]["text"] and "+20.00 pts (+20.0%)" in calls[-1]["json"]["text"]
    ev = m.track("NIFTY", 23199, T0 + timedelta(minutes=3), False, option_ltp=lambda s: 98.0)
    sent = [n.notify_event(e) for e in ev]
    assert [e.event for e in ev] == ["INVALIDATED", "CLOSED"] and sent == [False, True]
    assert "CLOSED: invalidated" in calls[-1]["json"]["text"]

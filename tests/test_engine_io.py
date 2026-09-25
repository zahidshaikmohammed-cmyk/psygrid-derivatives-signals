"""Engine I/O: logging, replay of the REAL inspected samples, CLI --once with a mocked client."""

import gzip
import json
from pathlib import Path

import run_engine
from psygrid.config import load_config
from psygrid.logger import EngineLogger
from psygrid.signal_engine import PsygridEngine
from psygrid.telegram_notifier import TelegramNotifier

from sim import SimMarket, bull_breakout_path

SAMPLES = Path(__file__).resolve().parent.parent / "samples" / "raw" / "20260924_103510"


def test_replay_real_samples_reports_actual_feed_states():
    cfg = load_config()
    eng = PsygridEngine(cfg)
    res = None
    for r in ("r1", "r2", "r3"):
        raws, ts = run_engine.load_replay_round(SAMPLES / r, cfg)
        res = eng.cycle(raws, local_now=ts)
    for idx, d in res.decisions.items():
        g = d.gate
        assert g.authorized and g.underlying_source == "OPTION_CHAIN.underlying_ltp"
        assert g.feeds["options"].state == "OK" and g.feeds["futures"].state == "BLOCKED"
        assert g.feeds["spot"].state == "BLOCKED" and g.feeds["indicators"].state == "BLOCKED"
        assert d.status == "WARMING_UP" and d.signal is None
    assert res.decisions["SENSEX"].gate.depth_mode == "QUOTE_ONLY"
    assert res.decisions["NIFTY"].gate.depth_mode == "FULL"


def test_logger_writes_decisions_raw_and_signals(tmp_path):
    cfg = load_config()
    lg = EngineLogger(cfg, tmp_path)
    eng = PsygridEngine(cfg, logger=lg, indices=("NIFTY",))
    sim = SimMarket(bull_breakout_path)
    for _ in range(70):
        raws, now, _, _ = sim.step_raws()
        eng.cycle(raws, local_now=now)
    day = tmp_path / "2026-09-24"
    assert (day / "decisions.jsonl").exists() and (day / "signals.jsonl").exists()
    assert (day / "events.jsonl").exists() and (day / "NIFTY_observations.jsonl").exists()
    sig = json.loads((day / "signals.jsonl").read_text().splitlines()[0])
    assert sig["direction"] == "CALL" and sig["setup"] == "BREAKOUT + ACCEPTANCE"
    raw_files = sorted((day / "raw").glob("*.json.gz"))
    assert len(raw_files) == 70
    bundle = json.loads(gzip.open(raw_files[0]).read())
    assert set(bundle) == {"nifty-spot", "nifty-options", "nifty-depth", "nifty-futures", "nifty-indicators"}
    assert json.loads(bundle["nifty-options"]["body"])["symbol"] == "NIFTY"


def test_cli_once_with_unreachable_endpoints(tmp_path, monkeypatch, capsys):
    import requests

    def boom(self, url, timeout):
        raise requests.ConnectTimeout("no route")
    monkeypatch.setattr(requests.Session, "get", boom)
    assert run_engine.main(["--once", "--no-color", "--log-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "PSYGRID OPTIONS ENGINE" in out
    assert out.count("BLOCKED") >= 3 or "MARKET CLOSED" in out


def test_notify_new_signals_fires_only_for_indices_with_a_new_signal():
    """`notify_new_signals` is the exact wiring point between run_engine.py's
    loop and the notifier - it must call notify_signal once per index whose
    `IndexDecision.signal` is set this cycle, and not at all for indices
    where it's None (WATCH/NO_TRADE/still-active-from-an-earlier-cycle)."""
    from psygrid.signal_engine import CycleResult, IndexDecision
    from test_signal_state import sig

    calls = []
    notified = sig()
    decisions = {
        "NIFTY": IndexDecision(index="NIFTY", ts=None, status="BUY_CALL", headline="BUY CALL",
                               signal=notified),
        "BANKNIFTY": IndexDecision(index="BANKNIFTY", ts=None, status="WATCH", headline="WATCH"),
        "SENSEX": IndexDecision(index="SENSEX", ts=None, status="SIGNAL_ACTIVE", headline="SIGNAL ACTIVE"),
    }
    res = CycleResult(ref_time=None, phase="NORMAL", decisions=decisions, events=[])

    class Notifier:
        def notify_signal(self, s):
            calls.append(s)

    run_engine.notify_new_signals(res, Notifier())
    assert calls == [notified]


def test_notify_new_signals_swallows_notifier_exceptions(capsys):
    """A broken notifier must never propagate out of the engine loop."""
    from psygrid.signal_engine import CycleResult, IndexDecision
    from test_signal_state import sig

    decisions = {"NIFTY": IndexDecision(index="NIFTY", ts=None, status="BUY_CALL",
                                        headline="BUY CALL", signal=sig())}
    res = CycleResult(ref_time=None, phase="NORMAL", decisions=decisions, events=[])

    class BrokenNotifier:
        def notify_signal(self, s):
            raise RuntimeError("boom")

    run_engine.notify_new_signals(res, BrokenNotifier())  # must not raise
    assert "boom" in capsys.readouterr().err


def test_cli_telegram_test_without_credentials_fails_cleanly(monkeypatch, capsys):
    monkeypatch.delenv("PSYGRID_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("PSYGRID_TELEGRAM_CHAT_ID", raising=False)
    assert run_engine.main(["--telegram-test"]) == 1
    assert "not configured" in capsys.readouterr().err


def test_cli_telegram_test_with_credentials_sends_message(monkeypatch, capsys):
    monkeypatch.setenv("PSYGRID_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PSYGRID_TELEGRAM_CHAT_ID", "12345")
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append((url, json))
        class R:
            status_code = 200
        return R()
    monkeypatch.setattr("requests.post", fake_post)

    assert run_engine.main(["--telegram-test"]) == 0
    assert "Test message sent." in capsys.readouterr().out
    assert len(calls) == 1 and "configured correctly" in calls[0][1]["text"]


def test_live_signal_triggers_a_telegram_notification(monkeypatch):
    """End-to-end: run the same bull-breakout simulation used by the logger
    test through PsygridEngine + notify_new_signals with Telegram enabled,
    proving the boundary hook actually fires on a real accepted signal, not
    just on a synthetic IndexDecision."""
    monkeypatch.setenv("PSYGRID_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PSYGRID_TELEGRAM_CHAT_ID", "12345")
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(json)
        class R:
            status_code = 200
        return R()
    monkeypatch.setattr("requests.post", fake_post)

    cfg = load_config()
    eng = PsygridEngine(cfg, indices=("NIFTY",))
    notifier = TelegramNotifier()
    sim = SimMarket(bull_breakout_path)
    for _ in range(70):
        raws, now, _, _ = sim.step_raws()
        res = eng.cycle(raws, local_now=now)
        run_engine.notify_new_signals(res, notifier)

    assert len(calls) == 1
    assert "NIFTY BUY CALL" in calls[0]["text"]


def test_live_put_signal_triggers_a_telegram_notification(monkeypatch):
    """Mirror of the CALL test above (sign=-1, same mirror-symmetry the
    engine itself uses in test_scenarios.py's ``bear`` fixture) - proves
    the accepted-signal -> Telegram boundary fires for BUY PUT too, not
    just BUY CALL, using the real production decision path."""
    monkeypatch.setenv("PSYGRID_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PSYGRID_TELEGRAM_CHAT_ID", "12345")
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(json)
        class R:
            status_code = 200
        return R()
    monkeypatch.setattr("requests.post", fake_post)

    cfg = load_config()
    eng = PsygridEngine(cfg, indices=("NIFTY",))
    notifier = TelegramNotifier()
    sim = SimMarket(bull_breakout_path, sign=-1)
    for _ in range(70):
        raws, now, _, _ = sim.step_raws()
        res = eng.cycle(raws, local_now=now)
        run_engine.notify_new_signals(res, notifier)

    assert len(calls) == 1
    assert "NIFTY BUY PUT" in calls[0]["text"]


def test_watch_and_no_trade_never_trigger_telegram_even_in_diagnostic_mode(monkeypatch):
    """Phase 11 / final acceptance criteria: WATCH, NO_TRADE and the
    --diagnostic near-miss trace must never reach Telegram - only a
    genuinely accepted TradeReadySignal-equivalent (dec.signal) does.
    Runs a scenario that produces WATCH/NO_TRADE with populated near-miss
    traces (not just silence) and confirms zero Telegram calls throughout,
    with --diagnostic rendering enabled (it only affects what the
    terminal prints, never notify_new_signals' input)."""
    from psygrid.monitor import Monitor

    monkeypatch.setenv("PSYGRID_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PSYGRID_TELEGRAM_CHAT_ID", "12345")
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(json)
        class R:
            status_code = 200
        return R()
    monkeypatch.setattr("requests.post", fake_post)

    cfg = load_config()
    eng = PsygridEngine(cfg, indices=("NIFTY",))
    notifier = TelegramNotifier()
    mon = Monitor(color=False, ascii_only=True, clear=False, diagnostic=True)
    sim = SimMarket(bull_breakout_path, sign=1)
    statuses = set()
    saw_trace = False
    for _ in range(50):  # stop before the breakout so it stays WATCH/NO_TRADE
        raws, now, _, _ = sim.step_raws()
        res = eng.cycle(raws, local_now=now)
        mon.render(res, eng.recent_events)          # diagnostic rendering happens
        run_engine.notify_new_signals(res, notifier)  # but never feeds Telegram
        d = res.decisions["NIFTY"]
        statuses.add(d.status)
        if d.trace and d.trace.setup_detected:
            saw_trace = True

    assert saw_trace, "scenario never reached a diagnosable setup - test would prove nothing"
    assert "BUY_CALL" not in statuses and "BUY_PUT" not in statuses
    assert calls == []

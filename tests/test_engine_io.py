"""Engine I/O: logging, replay of the REAL inspected samples, CLI --once with a mocked client."""

import gzip
import json
from pathlib import Path

import run_engine
from psygrid.config import load_config
from psygrid.logger import EngineLogger
from psygrid.signal_engine import PsygridEngine

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

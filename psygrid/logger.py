"""Timestamped research logs (JSON Lines), kept separate from the terminal.

logs/<YYYY-MM-DD>/
    engine.log                  human-readable runtime log
    decisions.jsonl             per index per cycle: gate, structure, levels, setups, scores, decision
    signals.jsonl               every emitted signal with full risk structure
    events.jsonl                signal state events (T1, T2, invalidation, close)
    data_quality.jsonl          every feed that was DEGRADED or BLOCKED
    <INDEX>_observations.jsonl  underlying price observations (reloaded on restart)
    raw/<HHMMSS>_cycleN.json.gz raw endpoint bodies + HTTP metadata, one bundle per cycle
"""

from __future__ import annotations

import dataclasses
import gzip
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .config import Config


def _default(o: Any) -> Any:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


class EngineLogger:
    def __init__(self, cfg: Config, root: Path | None = None):
        self.cfg = cfg["logging"]
        self.root = Path(root or self.cfg["dir"])
        self._day: str | None = None
        self.log = logging.getLogger("psygrid")
        self.log.setLevel(logging.INFO)
        self.log.propagate = False
        self.cycle = 0

    def day_dir(self, now: datetime) -> Path:
        day = now.strftime("%Y-%m-%d")
        d = self.root / day
        if day != self._day:
            d.mkdir(parents=True, exist_ok=True)
            for h in list(self.log.handlers):
                self.log.removeHandler(h)
                h.close()
            fh = logging.FileHandler(d / "engine.log", encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.log.addHandler(fh)
            self._day = day
        return d

    def observations_dir(self) -> Path:
        return self.root

    def write(self, kind: str, record: dict, now: datetime) -> None:
        path = self.day_dir(now) / f"{kind}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=_default, ensure_ascii=False) + "\n")

    def raw(self, raws: dict, now: datetime) -> None:
        """One gzip JSON bundle per cycle: every endpoint's metadata + raw body text."""
        self.cycle += 1
        if not self.cfg["raw_snapshots"] or (self.cycle - 1) % max(1, self.cfg["raw_every_n_cycles"]):
            return
        d = self.day_dir(now) / "raw"
        d.mkdir(exist_ok=True)
        bundle = {}
        for index, feeds in raws.items():
            for feed, r in feeds.items():
                bundle[f"{index.lower()}-{feed}"] = {
                    "url": r.url, "fetched_at": r.fetched_at, "http_status": r.http_status,
                    "elapsed_ms": r.elapsed_ms, "error": r.error, "server_date": r.server_date,
                    "body": r.body.decode("utf-8", errors="replace") if r.body is not None else None,
                }
        data = json.dumps(bundle, default=_default, ensure_ascii=False).encode("utf-8")
        name = f"{now:%H%M%S}_cycle{self.cycle}.json"
        if self.cfg["gzip_raw"]:
            with gzip.open(d / f"{name}.gz", "wb") as fh:
                fh.write(data)
        else:
            (d / name).write_bytes(data)

    def info(self, msg: str) -> None:
        self.log.info(msg)

    def warning(self, msg: str) -> None:
        self.log.warning(msg)

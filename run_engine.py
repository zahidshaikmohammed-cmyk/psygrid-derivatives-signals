"""PSYGRID OPTIONS ENGINE v1.0 — entry point (READ-ONLY signal mode).

    python run_engine.py                    continuous monitoring (Ctrl+C to stop)
    python run_engine.py --once             one cycle and exit
    python run_engine.py --interval 15      poll every 15 s
    python run_engine.py --replay samples/raw/20260924_103510
                                            replay saved snapshots through the engine
    python run_engine.py --config my.json   override config values
    python run_engine.py --no-color --ascii for plain consoles

This program never places orders. Output is BUY CALL / BUY PUT / NO TRADE
signal candidates with their reasoning and risk structure.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from psygrid.config import INDICES, load_config
from psygrid.data_client import FEEDS, DataClient, decode_payload
from psygrid.logger import EngineLogger
from psygrid.market_clock import IST, now_ist
from psygrid.models import RawResponse
from psygrid.monitor import Monitor, configure_stdout, enable_windows_ansi
from psygrid.schema_adapter import parse_ts
from psygrid.signal_engine import CycleResult, PsygridEngine
from psygrid.telegram_notifier import TelegramNotifier


def load_replay_round(rdir: Path, cfg) -> tuple[dict, datetime]:
    """Build RawResponses from an inspector round directory (rN/)."""
    raws: dict = {}
    fetched = []
    for index in INDICES:
        raws[index] = {}
        for feed in FEEDS:
            name = f"{cfg['endpoints']['prefix'][index]}{cfg['endpoints']['feeds'][feed]}"
            body_p, meta_p = rdir / f"{name}.json", rdir / f"{name}.meta.json"
            meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
            body = body_p.read_bytes() if body_p.exists() else None
            payload, err = decode_payload(body)
            ts = parse_ts(meta.get("requested_at_ist") or "") or now_ist()
            fetched.append(ts)
            date_hdr = (meta.get("headers") or {}).get("date")
            server = None
            if date_hdr:
                from email.utils import parsedate_to_datetime
                server = parsedate_to_datetime(date_hdr).astimezone(IST)
            raws[index][feed] = RawResponse(index=index, feed=feed, url=meta.get("url", str(body_p)),
                                            fetched_at=ts, http_status=meta.get("http_status"),
                                            elapsed_ms=meta.get("elapsed_ms"), body=body, payload=payload,
                                            error=meta.get("error") or err, server_date=server)
    return raws, max(fetched)


def notify_new_signals(res: CycleResult, notifier: TelegramNotifier) -> None:
    """Sends one Telegram message per index whose signal was newly accepted
    this cycle. ``IndexDecision.signal`` is only non-None in the exact
    cycle ``SignalStateManager.consider()`` returned ok=True for that
    index (see signal_engine.py), so this already fires at most once per
    accepted signal - no extra dedup needed here. Never allowed to affect
    the engine: any unexpected error is swallowed, matching how
    IndexPipeline.run() itself isolates a per-index failure."""
    for dec in res.decisions.values():
        if dec.signal is None:
            continue
        try:
            notifier.notify_signal(dec.signal)
        except Exception as exc:  # notification is never allowed to crash the engine
            print(f"[telegram] unexpected error sending notification: {type(exc).__name__}: {exc}",
                  file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PSYGRID OPTIONS ENGINE v1.0 (signals only, no orders)")
    ap.add_argument("--config", help="JSON file overriding psygrid/config.py defaults")
    ap.add_argument("--interval", type=float, help="poll interval seconds")
    ap.add_argument("--once", action="store_true", help="run one cycle and exit")
    ap.add_argument("--replay", type=Path, help="replay an inspector run directory (samples/raw/<run>)")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--ascii", action="store_true", help="ASCII symbols only")
    ap.add_argument("--no-clear", action="store_true", help="do not clear the screen between cycles")
    ap.add_argument("--log-dir", help="log directory (default: logs)")
    ap.add_argument("--telegram-test", action="store_true",
                    help="send a Telegram test message using PSYGRID_TELEGRAM_BOT_TOKEN / "
                         "PSYGRID_TELEGRAM_CHAT_ID from the environment, then exit")
    args = ap.parse_args(argv)

    if args.telegram_test:
        notifier = TelegramNotifier()
        if not notifier.enabled:
            print("Telegram notifications are not configured - set both PSYGRID_TELEGRAM_BOT_TOKEN "
                  "and PSYGRID_TELEGRAM_CHAT_ID.", file=sys.stderr)
            return 1
        ok = notifier.send_test_message()
        print("Test message sent." if ok else "Test message failed - see stderr for details.")
        return 0 if ok else 1

    configure_stdout()
    cfg = load_config(args.config)
    color = cfg["display"]["color"] and not args.no_color and sys.stdout.isatty() and enable_windows_ansi()
    mon = Monitor(color=color, ascii_only=args.ascii, clear=cfg["display"]["clear_screen"] and not args.no_clear
                  and not args.replay and not args.once, recent=cfg["display"]["recent_events"])
    logger = EngineLogger(cfg, Path(args.log_dir) if args.log_dir else None)

    if args.replay:
        rounds = sorted(p for p in args.replay.iterdir() if p.is_dir() and p.name.startswith("r"))
        if not rounds:
            print(f"no round directories (r1, r2, …) in {args.replay}")
            return 2
        eng = PsygridEngine(cfg, client=None, logger=None)
        for rdir in rounds:
            raws, ts = load_replay_round(rdir, cfg)
            res = eng.cycle(raws, local_now=ts)
            print(f"\n##### REPLAY {args.replay.name}/{rdir.name} #####")
            mon.show(res, eng.recent_events)
        return 0

    client = DataClient(cfg)
    eng = PsygridEngine(cfg, client=client, logger=logger)
    notifier = TelegramNotifier()
    interval = args.interval or cfg["poll_interval_seconds"]
    logger.info(f"engine start, interval {interval}s")
    print(f"PSYGRID OPTIONS ENGINE v1.0 — monitoring {', '.join(INDICES)} every {interval:g}s "
          f"(READ-ONLY signal mode). Fetching…")
    if notifier.enabled:
        print("Telegram notifications: enabled.")
    try:
        while True:
            t0 = time.monotonic()
            res = eng.cycle()
            mon.show(res, eng.recent_events)
            notify_new_signals(res, notifier)
            if args.once:
                break
            time.sleep(max(1.0, interval - (time.monotonic() - t0)))
    except KeyboardInterrupt:
        print("\nstopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())

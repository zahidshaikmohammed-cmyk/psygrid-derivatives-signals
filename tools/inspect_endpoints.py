"""PHASE 1 — live endpoint inspector for PSYGRID OPTIONS ENGINE.

Fetches every configured public endpoint, saves the raw bytes exactly as
received, and produces a recursive schema report describing what the JSON
actually contains. Nothing here assumes any field exists: every path in the
report comes from observed data.

Usage (from the project folder):

    python tools/inspect_endpoints.py                      # one round
    python tools/inspect_endpoints.py --rounds 3 --interval 20
    python tools/inspect_endpoints.py --from-dir samples/raw/20260924_101500

Outputs:
    samples/raw/<run_id>/r<N>/<name>.json        raw body, byte-for-byte
    samples/raw/<run_id>/r<N>/<name>.meta.json   HTTP status, timing, headers, error
    samples/schema/<run_id>/schema_report.md     human-readable schema
    samples/schema/<run_id>/schema.json          machine-readable schema
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

BASE_URL = "http://140.245.226.102:10000/public/"
INDICES = ("nifty", "banknifty", "sensex")
FEEDS = ("", "-options", "-depth", "-indicators", "-futures")

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent

MAX_EXAMPLES = 3
# A dict with at least this many keys, most of which look like numbers
# (e.g. strikes used as keys), is summarised as one dynamic-key entry.
DYNAMIC_KEY_MIN = 20
NUMERIC_KEY = re.compile(r"^-?\d+(\.\d+)?$")
TIMEY_NAME = re.compile(r"(time|timestamp|^ts$|_ts$|date|updated|asof|as_of)", re.I)


def endpoint_names() -> list[str]:
    return [f"{idx}{feed}" for idx in INDICES for feed in FEEDS]


# ----------------------------------------------------------------------------
# Fetching
# ----------------------------------------------------------------------------

def fetch(name: str, base_url: str = BASE_URL, timeout: float = 10.0) -> tuple[dict, bytes | None]:
    """Fetch one endpoint. Returns (meta, body). Never raises for network errors."""
    url = f"{base_url}{name}.json"
    requested = datetime.now(timezone.utc)
    meta: dict[str, Any] = {
        "name": name,
        "url": url,
        "requested_at_utc": requested.isoformat(),
        "requested_at_ist": requested.astimezone(IST).isoformat(),
        "http_status": None,
        "elapsed_ms": None,
        "headers": {},
        "bytes": 0,
        "error": None,
    }
    t0 = time.monotonic()
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        meta["elapsed_ms"] = round((time.monotonic() - t0) * 1000, 1)
        meta["error"] = f"{type(exc).__name__}: {exc}"
        return meta, None
    meta["elapsed_ms"] = round((time.monotonic() - t0) * 1000, 1)
    meta["http_status"] = resp.status_code
    meta["headers"] = {
        k: v for k, v in resp.headers.items()
        if k.lower() in {"content-type", "date", "last-modified", "etag", "cache-control", "age", "expires"}
    }
    meta["bytes"] = len(resp.content)
    return meta, resp.content


def parse_body(body: bytes | None) -> tuple[Any, str | None]:
    if body is None:
        return None, "no body"
    try:
        return json.loads(body.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


# ----------------------------------------------------------------------------
# Recursive schema inference
# ----------------------------------------------------------------------------

def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def _new_node() -> dict:
    return {
        "seen": 0,
        "types": Counter(),
        "examples": [],
        "num_min": None,
        "num_max": None,
        "zeros": 0,
        "empty_str": 0,
        "keys": {},          # dict children: key -> node
        "dynamic_keys": None,  # {"count_max": n, "sample": [...], "value": node}
        "list_len_min": None,
        "list_len_max": None,
        "items": None,       # list element node
    }


def merge(node: dict, value: Any) -> None:
    """Merge one observed value into a schema node (mutates node)."""
    node["seen"] += 1
    t = _type_name(value)
    node["types"][t] += 1

    if t in ("int", "float"):
        node["num_min"] = value if node["num_min"] is None else min(node["num_min"], value)
        node["num_max"] = value if node["num_max"] is None else max(node["num_max"], value)
        if value == 0:
            node["zeros"] += 1
    if t == "str" and value == "":
        node["empty_str"] += 1
    if t in ("int", "float", "str", "bool", "null"):
        if value not in node["examples"] and len(node["examples"]) < MAX_EXAMPLES:
            node["examples"].append(value if t != "str" else value[:80])

    if t == "dict":
        numeric = [k for k in value if NUMERIC_KEY.match(str(k))]
        if len(value) >= DYNAMIC_KEY_MIN and len(numeric) >= 0.8 * len(value):
            dyn = node["dynamic_keys"] or {"count_max": 0, "sample": [], "value": _new_node()}
            dyn["count_max"] = max(dyn["count_max"], len(value))
            for k in list(value)[:5]:
                if k not in dyn["sample"] and len(dyn["sample"]) < 5:
                    dyn["sample"].append(k)
            for k, v in value.items():
                if not NUMERIC_KEY.match(str(k)):
                    merge(node["keys"].setdefault(k, _new_node()), v)
                else:
                    merge(dyn["value"], v)
            node["dynamic_keys"] = dyn
        else:
            for k, v in value.items():
                merge(node["keys"].setdefault(k, _new_node()), v)

    if t == "list":
        n = len(value)
        node["list_len_min"] = n if node["list_len_min"] is None else min(node["list_len_min"], n)
        node["list_len_max"] = n if node["list_len_max"] is None else max(node["list_len_max"], n)
        if node["items"] is None:
            node["items"] = _new_node()
        for item in value:
            merge(node["items"], item)


def infer(value: Any) -> dict:
    node = _new_node()
    merge(node, value)
    return node


def timestamp_hint(path: str, node: dict) -> str | None:
    """Heuristic label only — the report says it must be verified by a human."""
    leaf = path.rsplit(".", 1)[-1].rstrip("[]")
    hints = []
    if TIMEY_NAME.search(leaf):
        hints.append("name looks time-related")
    for ex in node["examples"]:
        if isinstance(ex, (int, float)) and not isinstance(ex, bool):
            if 1_000_000_000 <= ex <= 2_500_000_000:
                hints.append("value in epoch-seconds range")
                break
            if 1_000_000_000_000 <= ex <= 2_500_000_000_000:
                hints.append("value in epoch-milliseconds range")
                break
        if isinstance(ex, str):
            try:
                datetime.fromisoformat(ex.replace("Z", "+00:00"))
                hints.append("parses as ISO-8601")
                break
            except ValueError:
                pass
    return ", ".join(hints) or None


def flatten(node: dict, path: str = "$", parent_seen: int | None = None) -> list[dict]:
    """Flatten a schema tree to rows (one per path)."""
    rows = [{
        "path": path,
        "types": dict(node["types"]),
        "present": node["seen"],
        "of": parent_seen if parent_seen is not None else node["seen"],
        "examples": node["examples"],
        "min": node["num_min"],
        "max": node["num_max"],
        "zeros": node["zeros"],
        "nulls": node["types"].get("null", 0),
        "empty_str": node["empty_str"],
        "list_len": (node["list_len_min"], node["list_len_max"]) if node["list_len_min"] is not None else None,
        "timestamp_hint": None,
    }]
    rows[0]["timestamp_hint"] = timestamp_hint(path, node)
    dict_seen = node["types"].get("dict", 0)
    for k, child in node["keys"].items():
        rows.extend(flatten(child, f"{path}.{k}", dict_seen))
    if node["dynamic_keys"]:
        dyn = node["dynamic_keys"]
        dyn_rows = flatten(dyn["value"], f"{path}.<numeric-key>", None)
        dyn_rows[0]["note"] = f"dynamic numeric keys, up to {dyn['count_max']} per object, e.g. {dyn['sample']}"
        rows.extend(dyn_rows)
    if node["items"] is not None:
        rows.extend(flatten(node["items"], f"{path}[]", None))
    return rows


def to_jsonable(node: dict) -> dict:
    out = {k: v for k, v in node.items() if k not in ("keys", "items", "dynamic_keys", "types")}
    out["types"] = dict(node["types"])
    out["keys"] = {k: to_jsonable(v) for k, v in node["keys"].items()}
    out["items"] = to_jsonable(node["items"]) if node["items"] is not None else None
    if node["dynamic_keys"]:
        d = node["dynamic_keys"]
        out["dynamic_keys"] = {"count_max": d["count_max"], "sample": d["sample"], "value": to_jsonable(d["value"])}
    else:
        out["dynamic_keys"] = None
    return out


# ----------------------------------------------------------------------------
# Change detection across rounds (freshness evidence)
# ----------------------------------------------------------------------------

def leaf_values(value: Any, path: str = "$", out: dict | None = None, limit: int = 5000) -> dict:
    out = {} if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(value, dict):
        for k, v in value.items():
            leaf_values(v, f"{path}.{k}", out, limit)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            leaf_values(v, f"{path}[{i}]", out, limit)
    else:
        out[path] = value
    return out


def changed_paths(rounds: list[Any]) -> dict[str, int]:
    """Count how many consecutive-round transitions changed each leaf path."""
    counts: Counter = Counter()
    flats = [leaf_values(r) for r in rounds if r is not None]
    for a, b in zip(flats, flats[1:]):
        for p in set(a) | set(b):
            if a.get(p) != b.get(p):
                counts[p] += 1
    return dict(counts)


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------

def _fmt(v: Any) -> str:
    s = json.dumps(v, ensure_ascii=False, default=str)
    return s.replace("|", "\\|")


def render_report(run_id: str, results: dict[str, dict]) -> str:
    lines = [
        "# PSYGRID live endpoint schema report",
        "",
        f"Run: `{run_id}` — generated {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST",
        "",
        "Every path below was observed in real responses. `present` counts how many",
        "parent objects contained the key. Timestamp hints are heuristics and must be",
        "verified by a human before the schema adapter relies on them.",
        "",
        "## Fetch summary",
        "",
        "| endpoint | HTTP | ms | bytes | JSON | top-level | error |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        m = r["metas"][-1]
        top = _type_name(r["parsed"][-1]) if r["parsed"] and r["parsed"][-1] is not None else "-"
        lines.append(
            f"| {name} | {m.get('http_status')} | {m.get('elapsed_ms')} | {m.get('bytes')} | "
            f"{'ok' if not r['parse_errors'][-1] else 'FAIL'} | {top} | "
            f"{_fmt(m.get('error') or r['parse_errors'][-1] or '')} |"
        )
    for name, r in results.items():
        lines += ["", f"## {name}", ""]
        m = r["metas"][-1]
        lines.append(f"- URL: `{m['url']}`")
        lines.append(f"- Headers: `{_fmt(m.get('headers'))}`")
        if r["schema"] is None:
            lines.append(f"- **No parseable JSON**: {r['parse_errors'][-1] or m.get('error')}")
            continue
        lines += [
            "",
            "| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        changes = r.get("changes", {})
        for row in flatten(r["schema"]):
            n_changed = sum(c for p, c in changes.items()
                            if re.sub(r"\[\d+\]", "[]", p) == row["path"])
            lines.append(
                f"| `{row['path']}` | {_fmt(row['types'])} | {row['present']}/{row['of']} | "
                f"{_fmt(row['examples'])} | {row['min'] if row['min'] is not None else ''} | "
                f"{row['max'] if row['max'] is not None else ''} | {row['zeros'] or ''} | {row['nulls'] or ''} | "
                f"{_fmt(row['list_len']) if row['list_len'] else ''} | {row['timestamp_hint'] or ''} | "
                f"{n_changed or ''} |"
            )
            if row.get("note"):
                lines.append(f"| ↳ note | {row['note']} ||||||||||")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def run_live(rounds: int, interval: float, timeout: float, base_url: str) -> tuple[str, dict]:
    run_id = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    raw_root = PROJECT_ROOT / "samples" / "raw" / run_id
    results: dict[str, dict] = {n: {"metas": [], "parsed": [], "parse_errors": []} for n in endpoint_names()}
    for rnd in range(1, rounds + 1):
        rdir = raw_root / f"r{rnd}"
        rdir.mkdir(parents=True, exist_ok=True)
        print(f"--- round {rnd}/{rounds} ---")
        for name in endpoint_names():
            meta, body = fetch(name, base_url, timeout)
            parsed, perr = parse_body(body)
            (rdir / f"{name}.meta.json").write_text(json.dumps({**meta, "parse_error": perr}, indent=2))
            if body is not None:
                (rdir / f"{name}.json").write_bytes(body)
            results[name]["metas"].append(meta)
            results[name]["parsed"].append(parsed)
            results[name]["parse_errors"].append(perr)
            status = meta["error"] or perr or "ok"
            print(f"  {name:<22} HTTP={meta['http_status']} {meta['elapsed_ms']}ms {meta['bytes']}B  {status}")
        if rnd < rounds:
            time.sleep(interval)
    return run_id, results


def load_dir(path: Path) -> tuple[str, dict]:
    """Re-analyse previously saved raw snapshots (offline)."""
    round_dirs = sorted(p for p in path.iterdir() if p.is_dir() and p.name.startswith("r")) or [path]
    results: dict[str, dict] = {}
    for rdir in round_dirs:
        for body_path in sorted(rdir.glob("*.json")):
            if body_path.name.endswith(".meta.json"):
                continue
            name = body_path.stem
            meta_path = rdir / f"{name}.meta.json"
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {
                "name": name, "url": str(body_path), "http_status": None, "elapsed_ms": None,
                "bytes": body_path.stat().st_size, "headers": {}, "error": None}
            parsed, perr = parse_body(body_path.read_bytes())
            r = results.setdefault(name, {"metas": [], "parsed": [], "parse_errors": []})
            r["metas"].append(meta)
            r["parsed"].append(parsed)
            r["parse_errors"].append(perr)
    return path.name, results


def build_schemas(results: dict) -> None:
    for r in results.values():
        good = [p for p in r["parsed"] if p is not None]
        if not good:
            r["schema"] = None
            continue
        node = _new_node()
        for p in good:
            merge(node, p)
        r["schema"] = node
        r["changes"] = changed_paths(good)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rounds", type=int, default=1, help="number of fetch rounds (>=2 shows which fields change)")
    ap.add_argument("--interval", type=float, default=15.0, help="seconds between rounds")
    ap.add_argument("--timeout", type=float, default=10.0, help="per-request timeout in seconds")
    ap.add_argument("--base-url", default=BASE_URL)
    ap.add_argument("--from-dir", type=Path, help="analyse saved snapshots instead of fetching")
    args = ap.parse_args(argv)

    if args.from_dir:
        run_id, results = load_dir(args.from_dir)
    else:
        run_id, results = run_live(args.rounds, args.interval, args.timeout, args.base_url)

    build_schemas(results)
    out_dir = PROJECT_ROOT / "samples" / "schema" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "schema_report.md").write_text(render_report(run_id, results), encoding="utf-8")
    (out_dir / "schema.json").write_text(json.dumps(
        {n: to_jsonable(r["schema"]) if r["schema"] else None for n, r in results.items()},
        indent=2, default=str), encoding="utf-8")
    print(f"\nSchema report: {out_dir / 'schema_report.md'}")

    reachable = sum(1 for r in results.values() if r["schema"] is not None)
    print(f"Endpoints with parseable JSON: {reachable}/{len(results)}")
    return 0 if reachable else 2


if __name__ == "__main__":
    sys.exit(main())

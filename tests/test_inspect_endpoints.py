"""Unit tests for the Phase-1 inspector. All network access is mocked.

The JSON shapes below are synthetic fixtures for exercising the schema walker;
they are NOT claims about what the live endpoints return.
"""

import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import inspect_endpoints as ie  # noqa: E402


class FakeResp:
    def __init__(self, status=200, content=b"{}", headers=None):
        self.status_code = status
        self.content = content
        self.headers = headers or {"Content-Type": "application/json", "X-Other": "drop"}


def test_endpoint_names_cover_all_15():
    names = ie.endpoint_names()
    assert len(names) == 15
    assert "nifty" in names and "sensex-depth" in names and "banknifty-futures" in names


def test_fetch_timeout_is_captured(monkeypatch):
    def boom(url, timeout):
        raise requests.Timeout("timed out")
    monkeypatch.setattr(ie.requests, "get", boom)
    meta, body = ie.fetch("nifty")
    assert body is None
    assert meta["http_status"] is None
    assert "Timeout" in meta["error"]


def test_fetch_connection_error_is_captured(monkeypatch):
    def boom(url, timeout):
        raise requests.ConnectionError("refused")
    monkeypatch.setattr(ie.requests, "get", boom)
    meta, body = ie.fetch("nifty-options")
    assert body is None and "ConnectionError" in meta["error"]


def test_fetch_http_error_keeps_body_and_filters_headers(monkeypatch):
    monkeypatch.setattr(ie.requests, "get", lambda url, timeout: FakeResp(500, b'{"x":1}'))
    meta, body = ie.fetch("nifty")
    assert meta["http_status"] == 500
    assert body == b'{"x":1}'
    assert "Content-Type" in meta["headers"] and "X-Other" not in meta["headers"]


@pytest.mark.parametrize("body", [b"not json", b"{\"a\": ", b"\xff\xfe"])
def test_parse_body_malformed(body):
    parsed, err = ie.parse_body(body)
    assert parsed is None and err


def test_parse_body_none():
    assert ie.parse_body(None) == (None, "no body")


def test_schema_merges_list_items_and_counts_presence():
    data = {"rows": [{"a": 1, "b": "x"}, {"a": 2.5}, {"a": 0, "b": None}]}
    rows = {r["path"]: r for r in ie.flatten(ie.infer(data))}
    a = rows["$.rows[].a"]
    assert a["present"] == 3 and a["of"] == 3
    assert a["types"] == {"int": 2, "float": 1}
    assert a["min"] == 0 and a["max"] == 2.5 and a["zeros"] == 1
    b = rows["$.rows[].b"]
    assert b["present"] == 2 and b["of"] == 3 and b["nulls"] == 1
    assert rows["$.rows"]["list_len"] == (3, 3)


def test_dynamic_numeric_keys_are_collapsed():
    data = {"chain": {str(20000 + 50 * i): {"v": i} for i in range(30)}}
    data["chain"]["meta"] = "keep"
    rows = {r["path"]: r for r in ie.flatten(ie.infer(data))}
    assert "$.chain.<numeric-key>" in rows
    assert "note" in rows["$.chain.<numeric-key>"]
    assert rows["$.chain.<numeric-key>.v"]["present"] == 30
    assert "$.chain.meta" in rows
    assert "$.chain.20000" not in rows


def test_small_numeric_key_dicts_not_collapsed():
    rows = {r["path"] for r in ie.flatten(ie.infer({"d": {"1": 1, "2": 2}}))}
    assert "$.d.1" in rows


def test_timestamp_hints_are_heuristic_labels():
    node = ie.infer(1_758_690_000)
    assert "epoch-seconds" in ie.timestamp_hint("$.x", node)
    node = ie.infer(1_758_690_000_000)
    assert "epoch-milliseconds" in ie.timestamp_hint("$.x", node)
    node = ie.infer("2026-09-24T10:14:27+05:30")
    assert "ISO" in ie.timestamp_hint("$.x", node)
    assert "name" in ie.timestamp_hint("$.updatedAt", ie.infer("abc"))
    assert ie.timestamp_hint("$.price", ie.infer(123.4)) is None


def test_changed_paths_across_rounds():
    r1 = {"p": 1, "q": [1, 2], "s": "a"}
    r2 = {"p": 2, "q": [1, 3], "s": "a"}
    r3 = {"p": 3, "q": [1, 3], "s": "a"}
    ch = ie.changed_paths([r1, r2, r3])
    assert ch["$.p"] == 2 and ch["$.q[1]"] == 1 and "$.s" not in ch


def test_main_offline_from_dir(tmp_path, monkeypatch):
    rdir = tmp_path / "run1" / "r1"
    rdir.mkdir(parents=True)
    (rdir / "nifty.json").write_text(json.dumps({"k": [{"z": 1}]}))
    (rdir / "nifty.meta.json").write_text(json.dumps({"name": "nifty", "url": "u", "http_status": 200,
                                                      "elapsed_ms": 5, "bytes": 10, "headers": {},
                                                      "error": None}))
    (rdir / "sensex.json").write_bytes(b"<html>")
    monkeypatch.setattr(ie, "PROJECT_ROOT", tmp_path)
    assert ie.main(["--from-dir", str(tmp_path / "run1")]) == 0
    report = (tmp_path / "samples" / "schema" / "run1" / "schema_report.md").read_text()
    assert "`$.k[].z`" in report
    assert "No parseable JSON" in report
    schema = json.loads((tmp_path / "samples" / "schema" / "run1" / "schema.json").read_text())
    assert schema["sensex"] is None and schema["nifty"]["keys"]["k"]["items"]["keys"]["z"]


def test_main_live_all_unreachable_returns_2(tmp_path, monkeypatch):
    def boom(url, timeout):
        raise requests.ConnectTimeout("x")
    monkeypatch.setattr(ie.requests, "get", boom)
    monkeypatch.setattr(ie, "PROJECT_ROOT", tmp_path)
    assert ie.main(["--rounds", "1"]) == 2
    metas = list((tmp_path / "samples" / "raw").rglob("*.meta.json"))
    assert len(metas) == 15

import requests

from psygrid.config import load_config
from psygrid.data_client import DataClient, endpoint_url


class Resp:
    def __init__(self, status, content, headers=None):
        self.status_code, self.content = status, content
        self.headers = headers or {"Date": "Thu, 24 Sep 2026 05:05:50 GMT"}


def client(fn):
    return DataClient(load_config(), getter=fn)


def test_urls_match_documented_endpoints():
    cfg = load_config()
    assert endpoint_url(cfg, "NIFTY", "spot") == "http://140.245.226.102:10000/public/nifty.json"
    assert endpoint_url(cfg, "BANKNIFTY", "options") == "http://140.245.226.102:10000/public/banknifty-options.json"
    assert endpoint_url(cfg, "SENSEX", "futures") == "http://140.245.226.102:10000/public/sensex-futures.json"


def test_timeout_returns_unavailable_after_retry():
    calls = []

    def boom(url, timeout):
        calls.append(url)
        raise requests.Timeout("read timed out")
    r = client(boom).fetch("NIFTY", "options")
    assert r.payload is None and r.http_status is None and "Timeout" in r.error
    assert len(calls) == 2          # 1 retry


def test_connection_error():
    def boom(url, timeout):
        raise requests.ConnectionError("refused")
    r = client(boom).fetch("NIFTY", "depth")
    assert "endpoint unavailable" in r.error


def test_http_503_keeps_json_payload():
    r = client(lambda u, timeout: Resp(503, b'{"status": "ERROR", "symbol": "NIFTY"}')).fetch("NIFTY", "futures")
    assert r.http_status == 503 and r.payload["status"] == "ERROR" and r.error is None
    assert r.server_date is not None and r.server_date.hour == 10


def test_malformed_json():
    r = client(lambda u, timeout: Resp(200, b"<html>oops")).fetch("NIFTY", "spot")
    assert r.payload is None and "malformed JSON" in r.error


def test_fetch_all_covers_15_endpoints():
    res = client(lambda u, timeout: Resp(200, b"{}")).fetch_all()
    assert sum(len(v) for v in res.values()) == 15

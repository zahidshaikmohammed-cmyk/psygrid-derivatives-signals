"""Deterministic market simulator for tests.

Every payload is produced by editing a trimmed copy of a REAL live response
(tests/fixtures, taken from samples/raw/20260924_103510), so the engine is
exercised against the exact observed schema. Prices, flows and books are
synthetic test data.

Mirror symmetry: with ``sign=-1`` every price is reflected around ``center``
(p -> 2*center - p), CE and PE roles swap, and futures basis changes flip.
A symmetric engine must then produce the opposite direction with the same
quality score — this is the anti-bias test.
"""

from __future__ import annotations

import copy
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from psygrid.market_clock import IST
from psygrid.models import RawResponse

FIX = Path(__file__).parent / "fixtures"


def fixture(name: str) -> dict:
    return json.loads((FIX / f"{name}.json").read_text())


def tri(t: float, period: float) -> float:
    """Triangle wave in [-1, 1]."""
    x = (t / period) % 1.0
    return 4 * x - 1 if x < 0.5 else 3 - 4 * x


def bull_breakout_path(i: int) -> tuple[float, str]:
    """Bullish template, one point per 20 s poll. Returns (price, phase)."""
    t = i / 3.0                                  # minutes
    if t < 18:
        return 23171 + 20 * tri(t + 1, 4), "range"   # range 23151-23191 under 23200
    if t < 20:
        k = (t - 18) / 2
        return 23171 + (23216 - 23171) * k, "breakout"
    if t < 27:
        return 23216 + 1.6 * (t - 20) * 3, "hold"      # grind higher, accepted above
    return 23216 + 1.6 * 21 + 3.0 * (t - 27) * 3, "trend"


def failed_breakout_path(i: int) -> tuple[float, str]:
    """Slow range under 23200, a push through it that cannot hold, then a drop."""
    t = i / 3.0
    if t < 24:
        return 23160 + 30 * tri(t + 2.5, 10), "range"          # 23130-23190
    if t < 26:
        return 23175 + (23212 - 23175) * (t - 24) / 2, "fake"    # push through the level
    if t < 27:
        return 23212, "fake"
    if t < 29:
        return 23212 - (23212 - 23180) * (t - 27) / 2, "fail"    # back below the level
    return 23180 - 4.0 * (t - 29), "drop"


def chop_path(i: int) -> tuple[float, str]:
    t = i / 3.0
    return 23205 + 9 * math.sin(t * 1.3) + 4 * math.sin(t * 3.7), "chop"


class SimMarket:
    def __init__(self, path=bull_breakout_path, sign: int = 1, center: float = 23200.0,
                 start: datetime | None = None, futures_ok: bool = True, indicators_ok: bool = True,
                 depth_ok: bool = True, flows: bool = True, step: float = 50.0,
                 flow_map: dict | None = None, depth_flow_map: dict | None = None):
        self.path, self.sign, self.C = path, sign, center
        self.start = start or datetime(2026, 9, 24, 10, 0, 0, tzinfo=IST)
        self.futures_ok, self.indicators_ok, self.depth_ok, self.flows = futures_ok, indicators_ok, depth_ok, flows
        self.step = step
        self.flow_map = flow_map if flow_map is not None else {"breakout": 1, "hold": 1, "trend": 1}
        self.depth_flow_map = depth_flow_map if depth_flow_map is not None else self.flow_map
        self.tpl = {n: fixture(n) for n in ("nifty", "nifty-options", "nifty-depth", "nifty-futures",
                                             "banknifty-indicators", "nifty-indicators")}
        self.i = -1
        self.cum_vol: dict = {}
        self.oi: dict = {}
        self.closes: list[float] = []
        self.minute_close: dict = {}
        self.prices: list[float] = []

    # ------------------------------------------------------------- helpers
    def price(self, i: int) -> tuple[float, str]:
        p, ph = self.path(i)
        return (p if self.sign > 0 else 2 * self.C - p), ph

    def now(self, i: int) -> datetime:
        return self.start + timedelta(seconds=20 * i)

    def strikes(self) -> list[float]:
        return [self.C + k * self.step for k in range(-15, 16)]

    @staticmethod
    def premium(x: float) -> float:
        """x = moneyness in the option's favour (S-K for CE, K-S for PE)."""
        return max(x, 0.0) + 60.0 * math.exp(-0.5 * (x / 150.0) ** 2)

    @staticmethod
    def delta(x: float) -> float:
        return 1 / (1 + math.exp(-x / 90.0))

    def role(self, otype: str, flow: int = 1) -> str:
        """'bull' side (CE in the bullish template) or 'bear' side, mirrored
        by ``sign`` and by the phase flow direction."""
        eff = self.sign * (flow or 1)
        return ("bull" if otype == "CE" else "bear") if eff > 0 else ("bear" if otype == "CE" else "bull")

    def flow(self, phase: str, depth: bool = False) -> int:
        if not self.flows:
            return 0
        return (self.depth_flow_map if depth else self.flow_map).get(phase, 0)

    def mk(self, k: float) -> float:
        """Mirror a strike into template coordinates (distance from center in bull frame)."""
        return (k - self.C) * self.sign

    # ------------------------------------------------------------ payloads
    def options(self, S: float, phase: str, now: datetime) -> dict:
        p = copy.deepcopy(self.tpl["nifty-options"])
        rows, contracts = [], []
        f = self.flow(phase)
        active = f != 0
        tot_c = tot_p = 0.0
        sid = 50000
        for k in self.strikes():
            row = {"strike": k}
            for otype, key in (("CE", "ce"), ("PE", "pe")):
                x = (S - k) if otype == "CE" else (k - S)
                prem = round(self.premium(x) / 0.05) * 0.05
                d = self.delta(x)
                g = d * (1 - d) / 90.0
                role = self.role(otype)
                frole = self.role(otype, f)
                m = self.mk(k)
                # base OI profile in bull-template coordinates: bull-side big OI at the level (m=0),
                # bear-side big OI 200 points below it
                if role == "bull":
                    base_oi = 9_000_000 if m == 0 else 1_500_000
                else:
                    base_oi = 8_000_000 if m == -200 else 1_500_000
                keyc = (k, otype)
                self.oi.setdefault(keyc, float(base_oi))
                near = abs(k - S) <= 2 * self.step
                if active and near:
                    self.oi[keyc] += 60_000 if frole == "bear" else -20_000   # bear-side writing
                vol_inc = 20_000 if near else 2_000
                if active and near:
                    vol_inc *= 3 if frole == "bull" else 1.2
                self.cum_vol[keyc] = self.cum_vol.get(keyc, 1_000_000.0) + vol_inc
                bid = max(0.05, round((prem - 0.05) / 0.05) * 0.05)
                ask = round((bid + 0.10) / 0.05) * 0.05
                sid += 1
                row[key] = {
                    "average_price": prem, "greeks": {"delta": round(d if otype == "CE" else -d, 5),
                                                      "theta": -10.0, "gamma": round(g, 6), "vega": 10.0},
                    "implied_volatility": 12.0, "last_price": prem, "oi": int(self.oi[keyc]),
                    "previous_close_price": prem, "previous_oi": int(base_oi * 0.8),
                    "previous_volume": 1_000_000, "security_id": sid,
                    "top_ask_price": ask, "top_ask_quantity": 650, "top_bid_price": bid,
                    "top_bid_quantity": 650, "volume": int(self.cum_vol[keyc]),
                }
                contracts.append({"security_id": sid, "strike": k, "option_type": otype, "moneyness":
                                  "ITM" if x > 0 else "OTM", "oi": float(self.oi[keyc]),
                                  "volume": float(self.cum_vol[keyc]), "last_price": float(prem),
                                  "implied_volatility": 12.0, "oi_change_classification": "LONG_BUILDUP"})
                if otype == "CE":
                    tot_c += self.cum_vol[keyc]
                else:
                    tot_p += self.cum_vol[keyc]
            rows.append(row)
        p.update(underlying_ltp=round(S, 2), updated_at=(now - timedelta(seconds=1)).isoformat(),
                 fetch_count=1000 + self.i, strikes=rows, expiry="2026-09-29")
        a = p["analytics"]
        a.update(atm_strike=min(self.strikes(), key=lambda k: abs(k - S)), contracts=contracts,
                 resistance_strikes=[self.C + 700 * self.sign], support_strikes=[self.C - 700 * self.sign],
                 max_pain_strike=self.C - 650 * self.sign, total_call_volume=tot_c, total_put_volume=tot_p)
        return p

    def depth(self, S: float, phase: str, now: datetime) -> dict:
        p = copy.deepcopy(self.tpl["nifty-depth"])
        f = self.flow(phase, depth=True)
        active = f != 0
        atm = min(self.strikes(), key=lambda k: abs(k - S))
        out = []
        for k in [atm + j * self.step for j in range(-2, 3)]:
            for otype in ("CE", "PE"):
                x = (S - k) if otype == "CE" else (k - S)
                prem = round(self.premium(x) / 0.05) * 0.05
                role = self.role(otype, f)
                bq, aq = 1000, 1000
                if active:
                    bq, aq = (2000, 1000) if role == "bull" else (1000, 2000)
                c = copy.deepcopy(p["contracts"][0])
                c.update(strike=k, option_type=otype, last_price=prem, buy_quantity=bq * 20,
                         sell_quantity=aq * 20, quote_updated_at=(now - timedelta(seconds=1)).isoformat(),
                         updated_at=(now - timedelta(seconds=1)).isoformat(), crossed_book=False,
                         bid=[{"level": j + 1, "price": round(prem - 0.05 * (j + 1), 2), "quantity": bq,
                               "orders": 3} for j in range(20)],
                         ask=[{"level": j + 1, "price": round(prem + 0.05 * (j + 1), 2), "quantity": aq,
                               "orders": 3} for j in range(20)])
                out.append(c)
        p.update(contracts=out, contract_count=len(out), underlying_ltp=round(S, 2),
                 updated_at=(now - timedelta(seconds=1)).isoformat(), status="LIVE")
        if not self.depth_ok:
            p.update(status="ERROR", updated_at=None, error="WebSocketConnectionClosedException: test")
            for c in p["contracts"]:
                c["bid"], c["ask"] = [], []
                c["quote_updated_at"] = (now - timedelta(minutes=10)).isoformat()
        return p

    def futures(self, S: float, phase: str, now: datetime) -> dict:
        p = copy.deepcopy(self.tpl["nifty-futures"])
        if not self.futures_ok:
            return p                                    # real observed ERROR payload
        self._basis = getattr(self, "_basis", 60.0) + 0.5 * self.sign * self.flow(phase)
        f = S + self._basis
        p.update(status="LIVE", error=None, last_price=round(f, 2), trading_symbol="NIFTY-TEST-FUT",
                 expiry="2026-09-29", ohlc={"open": 23230.0, "high": max(f, 23260.0), "low": min(f, 23180.0),
                                            "close": 23200.0},
                 volume=1_000_000 + self.i * 1000, oi=12_000_000, oi_change=0, average_price=round(f - 5, 2),
                 buy_quantity=100000, sell_quantity=100000, top_bid_price=round(f - 0.5, 2),
                 top_ask_price=round(f + 0.5, 2), updated_at=(now - timedelta(seconds=1)).isoformat())
        # no futures-derived levels in the scenario (keeps the mirror exact)
        p["ohlc"], p["average_price"] = None, None
        return p

    def indicators(self, now: datetime) -> dict:
        if not self.indicators_ok:
            return copy.deepcopy(self.tpl["nifty-indicators"])     # real STARTING payload
        p = copy.deepcopy(self.tpl["banknifty-indicators"])
        p["symbol"] = p["result"]["symbol"] = "NIFTY"
        cur_min = now.replace(second=0, microsecond=0)
        closes = [c for m, c in sorted(self.minute_close.items()) if m < cur_min]
        if not closes:
            return copy.deepcopy(self.tpl["nifty-indicators"])
        def ema(vals, n):
            k, e = 2 / (n + 1), vals[0]
            for v in vals[1:]:
                e = v * k + e * (1 - k)
            return e
        r = p["result"]
        r["as_of"] = (cur_min - timedelta(minutes=1)).isoformat()
        r["last_price"] = closes[-1]
        r["bar_count"] = len(closes)
        ind, st = r["indicators"], r["indicator_status"]
        ind["vwap"] = sum(self.prices) / len(self.prices)
        st["vwap"]["ready"] = True
        if len(closes) >= 20:
            ind["ema_9"], ind["ema_20"] = ema(closes, 9), ema(closes, 20)
            st["ema_9"]["ready"] = st["ema_20"]["ready"] = True
        return p

    def spot(self, now: datetime) -> dict:
        p = copy.deepcopy(self.tpl["nifty"])
        p["session"]["current_time_ist"] = now.strftime("%Y-%m-%d %H:%M:%S IST")
        return p                                        # real observed: ltp null, no candles

    # ---------------------------------------------------------------- step
    def step_raws(self) -> tuple[dict, datetime, float, str]:
        self.i += 1
        now = self.now(self.i)
        S, phase = self.price(self.i)
        self.prices.append(S)
        self.minute_close[now.replace(second=0, microsecond=0)] = S
        payloads = {"spot": self.spot(now), "options": self.options(S, phase, now),
                    "depth": self.depth(S, phase, now), "futures": self.futures(S, phase, now),
                    "indicators": self.indicators(now)}
        raws = {}
        for feed, pl in payloads.items():
            body = json.dumps(pl).encode()
            status = 200
            if pl.get("status") in ("ERROR", "STARTING"):
                status = 503
            raws[feed] = RawResponse(index="NIFTY", feed=feed, url=f"sim://{feed}", fetched_at=now,
                                     http_status=status, elapsed_ms=5.0, body=body, payload=pl, error=None)
        return {"NIFTY": raws}, now, S, phase

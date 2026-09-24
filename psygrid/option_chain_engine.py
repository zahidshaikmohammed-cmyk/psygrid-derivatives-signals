"""Option-chain intelligence: strike map around ATM, contract quality,
intraday participation flows and OI maps.

The chain carries no aggressor side, so participation is treated as
*evidence*, built from three intraday deltas measured between our own polls
over ATM +/- 2 strikes:

* OI flow      put-OI build vs call-OI build (put writing = supportive)
* volume flow  call vs put traded-volume dominance
* premium flow ATM call vs put premium % change (partly underlying-driven,
               hence the smallest weight)

Day-level context (server ``oi_change_classification``, OI vs previous_oi)
is reported but not used as an intraday trigger.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from statistics import mean, median
from typing import Optional

from .config import Config
from .models import OptionChain, OptionQuote


@dataclass
class ContractView:
    quote: OptionQuote
    accepted: bool
    reject_reasons: list[str]
    liquidity: float           # 0..1 relative within window


@dataclass
class ChainState:
    available: bool
    step: Optional[float] = None
    atm: Optional[float] = None
    server_atm: Optional[float] = None
    window: list[float] = field(default_factory=list)
    contracts: dict[tuple[float, str], ContractView] = field(default_factory=dict)
    participation: Optional[float] = None        # -1..1 bullish positive
    participation_parts: dict[str, float] = field(default_factory=dict)
    activity_expansion: Optional[float] = None   # 0..1
    activity_ratio: Optional[float] = None
    call_resistance_map: list[tuple[float, float]] = field(default_factory=list)
    put_support_map: list[tuple[float, float]] = field(default_factory=list)
    pcr_oi: Optional[float] = None
    day_oi_context: dict[str, int] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


def infer_step(strikes: list[float], price: float) -> Optional[float]:
    near = sorted(k for k in strikes if abs(k - price) <= price * 0.03)
    diffs = [round(b - a, 2) for a, b in zip(near, near[1:]) if b > a]
    if not diffs:
        return None
    return Counter(diffs).most_common(1)[0][0]


def _clip(x: float) -> float:
    return max(-1.0, min(1.0, x))


class OptionChainEngine:
    def __init__(self, cfg: Config, index: str):
        self.cfg = cfg
        self.c = cfg["options"]
        self.index = index
        self.hist: deque = deque(maxlen=30)

    def analyze(self, chain: Optional[OptionChain], usable: bool, price: Optional[float]) -> ChainState:
        if not usable or chain is None or price is None:
            return ChainState(available=False, reasons=["option chain unavailable"])
        st = ChainState(available=True)
        st.step = infer_step(chain.strikes, price)
        if st.step is None:
            return ChainState(available=False, reasons=["cannot infer strike step near price"])
        st.atm = min(chain.strikes, key=lambda k: abs(k - price))
        st.server_atm = chain.analytics.atm_strike if chain.analytics else None
        st.pcr_oi = chain.analytics.pcr_oi if chain.analytics else None
        n = self.c["strike_window"]
        st.window = [k for k in chain.strikes if abs(k - st.atm) <= n * st.step + 1e-6]

        # ---- contract validation
        vols = [q.volume for (k, _), q in chain.quotes.items() if k in st.window and q.volume]
        med_vol = median(vols) if vols else 0
        max_oi = max((q.oi or 0 for (k, _), q in chain.quotes.items() if k in st.window), default=0) or 1
        for k in st.window:
            for t in ("CE", "PE"):
                q = chain.quote(k, t)
                if q is None:
                    continue
                rr = []
                if q.ltp is None:
                    rr.append("no LTP")
                if q.bid is None or q.ask is None:
                    rr.append("no two-sided quote")
                elif q.ask < q.bid:
                    rr.append("crossed quote")
                elif q.spread_pct is not None and q.spread_pct > self.c["max_spread_pct"]:
                    rr.append(f"spread {q.spread_pct:.2f}% > {self.c['max_spread_pct']}%")
                if not q.volume:
                    rr.append("no volume")
                elif med_vol and q.volume < self.c["min_volume_vs_median"] * med_vol:
                    rr.append("volume far below window median")
                if not q.oi:
                    rr.append("no OI")
                liq = 0.0
                if q.volume and med_vol:
                    liq = min(1.0, 0.6 * min(q.volume / med_vol, 2) / 2 + 0.4 * (q.oi or 0) / max_oi)
                st.contracts[(k, t)] = ContractView(q, not rr, rr, round(liq, 3))

        # ---- OI maps (positioning evidence, not guaranteed levels)
        ce = sorted(((k, chain.quote(k, "CE").oi) for k in st.window
                     if k >= price and chain.quote(k, "CE") and chain.quote(k, "CE").oi), key=lambda x: -x[1])
        pe = sorted(((k, chain.quote(k, "PE").oi) for k in st.window
                     if k <= price and chain.quote(k, "PE") and chain.quote(k, "PE").oi), key=lambda x: -x[1])
        st.call_resistance_map, st.put_support_map = ce[:3], pe[:3]
        if chain.analytics:
            near = {(k, t): v for (k, t), v in chain.analytics.oi_change_class.items()
                    if abs(k - st.atm) <= 2 * st.step + 1e-6}
            st.day_oi_context = dict(Counter(f"{t}:{v}" for (k, t), v in near.items()))

        # ---- intraday flows from our own poll history
        core = [k for k in st.window if abs(k - st.atm) <= 2 * st.step + 1e-6]
        snap = {"ts": chain.updated_at, "q": {}, "atm": st.atm}
        for k in core:
            for t in ("CE", "PE"):
                q = chain.quote(k, t)
                if q is not None:
                    snap["q"][(k, t)] = (q.volume, q.oi, q.ltp)
        tot = (chain.analytics.total_call_volume, chain.analytics.total_put_volume) if chain.analytics else (None, None)
        snap["tot"] = (tot[0] + tot[1]) if None not in tot else None
        if not self.hist or self.hist[-1]["ts"] != chain.updated_at:
            self.hist.append(snap)
        self._flows(st, core)
        return st

    def _flows(self, st: ChainState, core: list[float]) -> None:
        polls = self.c["participation_polls"]
        if len(self.hist) < 2:
            st.reasons.append("building option-flow history")
            return
        old = self.hist[max(0, len(self.hist) - 1 - polls)]
        new = self.hist[-1]
        d = {"CE": [0.0, 0.0], "PE": [0.0, 0.0]}      # [dVol, dOI]
        prem: dict[str, list[float]] = {"CE": [], "PE": []}
        for key, (v1, oi1, p1) in new["q"].items():
            if key not in old["q"]:
                continue
            v0, oi0, p0 = old["q"][key]
            t = key[1]
            if v1 is not None and v0 is not None and v1 >= v0:
                d[t][0] += v1 - v0
            if oi1 is not None and oi0 is not None:
                d[t][1] += oi1 - oi0
            if p1 and p0 and key[0] == st.atm:
                prem[t].append((p1 - p0) / p0)
        parts = {}
        s_vol = d["CE"][0] + d["PE"][0]
        if s_vol > 0:
            parts["volume_flow"] = (d["CE"][0] - d["PE"][0]) / s_vol
        s_oi = abs(d["CE"][1]) + abs(d["PE"][1])
        if s_oi > 0:
            parts["oi_flow"] = _clip((d["PE"][1] - d["CE"][1]) / s_oi)
        if prem["CE"] and prem["PE"]:
            parts["premium_flow"] = _clip((mean(prem["CE"]) - mean(prem["PE"])) * 20)
        wts = {"oi_flow": 0.5, "volume_flow": 0.35, "premium_flow": 0.15}
        if parts:
            tw = sum(wts[k] for k in parts)
            st.participation = round(sum(wts[k] * v for k, v in parts.items()) / tw, 3)
            st.participation_parts = {k: round(v, 3) for k, v in parts.items()}

        # activity expansion: latest total-volume delta vs earlier per-poll deltas
        tots = [h["tot"] for h in self.hist if h["tot"] is not None]
        deltas = [b - a for a, b in zip(tots, tots[1:]) if b >= a]
        if len(deltas) >= 4 and mean(deltas[:-1]) > 0:
            ratio = deltas[-1] / mean(deltas[:-1])
            st.activity_ratio = round(ratio, 2)
            st.activity_expansion = round(max(0.0, min(1.0, ratio - 1.0)), 3)
        else:
            st.reasons.append("activity baseline not ready")

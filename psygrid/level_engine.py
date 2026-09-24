"""INTELLIGENT MARKET LEVEL ENGINE — a primary decision layer.

Pipeline per cycle
    1. discover candidate prices from independent evidence families
    2. cluster nearby candidates into ZONES (never dozens of near-identical lines)
    3. match zones to the persistent registry (stable IDs such as NIFTY_L_003)
    4. score strength 0-100 (configurable weights) and assign tier 1/2/3
    5. advance each zone's state machine with the new price / completed bars
    6. describe price-to-level relationships for the setup engine

Evidence is only taken from verified data. Levels whose source feed is not
available (e.g. previous-day levels when no historical candles exist, futures
levels while the futures feed is in ERROR) are simply not created.

State machine (events are recorded with timestamps for the setup engine):
    UNTESTED -> APPROACHING -> TESTING -> REJECTED            (held)
                                      -> BROKEN -> ACCEPTED   (N closes beyond)
                                                -> FAILED_BREAKOUT / FAILED_BREAKDOWN
    ACCEPTED / RECLAIMED -> TESTING (retest) -> REJECTED (retest held) | BROKEN
    a break that is accepted in the direction opposite to an earlier accepted
    break is RECLAIMED; zones that lose all evidence and stay far away become
    INVALIDATED and are dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .config import Config
from .liquidity_engine import find_pools
from .models import Candle, OptionChain
from .structure_engine import StructureState, find_swings_segmented

FAMILY = {
    "PDH": "PREV_DAY", "PDL": "PREV_DAY", "PDC": "PREV_DAY", "PDO": "PREV_DAY",
    "SESSION_HIGH": "SESSION", "SESSION_LOW": "SESSION",
    "OPENING_RANGE_HIGH": "OPENING_RANGE", "OPENING_RANGE_LOW": "OPENING_RANGE",
    "SWING": "SWING", "VWAP": "VWAP",
    "OI_CE": "OPTIONS", "OI_PE": "OPTIONS", "OICHG_CE": "OPTIONS", "OICHG_PE": "OPTIONS",
    "SERVER_OI": "OPTIONS", "MAX_PAIN": "OPTIONS",
    "FUTURES": "FUTURES", "ROUND": "ROUND", "LIQUIDITY_POOL": "LIQUIDITY",
    "SUPPLY_DEMAND": "SUPPLY_DEMAND",
}
FAMILY_CAP = {"OPTIONS": 28, "SWING": 20, "PREV_DAY": 30, "ROUND": 7}
TF_RANK = {"DAILY": 6, "1h": 5, "15m": 4, "5m": 3, "SESSION": 2, "1m": 1, "OPTIONS": 1, "STATIC": 0}

BREAK_STATES = ("BROKEN",)
TERMINAL = ("REJECTED", "ACCEPTED", "RECLAIMED", "FAILED_BREAKOUT", "FAILED_BREAKDOWN")


@dataclass
class Candidate:
    price: float
    category: str
    label: str
    timeframe: str
    weight: float
    ts: Optional[datetime] = None          # when the evidence formed (None = static)
    half_width: float = 0.0


@dataclass
class LevelEvent:
    ts: datetime
    event: str             # TESTING, REJECTED, BROKEN, ACCEPTED, RECLAIMED, FAILED_BREAKOUT, ...
    direction: Optional[str]   # UP | DOWN
    price: float
    note: str = ""


@dataclass
class Zone:
    id: str
    low: float
    high: float
    center: float
    candidates: list[Candidate] = field(default_factory=list)
    strength: float = 0.0
    tier: int = 3
    timeframe: str = "STATIC"
    families: list[str] = field(default_factory=list)
    kind: str = "RESISTANCE"               # SUPPORT | RESISTANCE (relative to price)
    origin_kind: Optional[str] = None
    state: str = "UNTESTED"
    state_ts: Optional[datetime] = None
    events: list[LevelEvent] = field(default_factory=list)
    tests: int = 0
    rejections: int = 0
    entered_from: Optional[str] = None     # UNDER | OVER
    last_outside: Optional[str] = None
    break_dir: Optional[str] = None
    break_ts: Optional[datetime] = None
    break_extreme: Optional[float] = None
    closes_beyond: int = 0
    bars_since_break: int = 0
    accepted_dir: Optional[str] = None     # last accepted break direction
    retest_of: Optional[str] = None        # accepted direction being retested
    last_bar_ts: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    earliest_ts: Optional[datetime] = None
    last_price: Optional[float] = None
    pre_approach_state: Optional[str] = None
    first_seen: Optional[datetime] = None

    @property
    def sources(self) -> list[str]:
        seen, out = set(), []
        for c in sorted(self.candidates, key=lambda c: -c.weight):
            if c.label not in seen:
                seen.add(c.label)
                out.append(c.label)
        return out

    @property
    def role_label(self) -> str:
        zone_kind = self.kind
        if any(FAMILY[c.category] == "SUPPLY_DEMAND" for c in self.candidates):
            zone_kind = "DEMAND" if self.kind == "SUPPORT" else "SUPPLY"
        prefix = "MAJOR " if self.tier == 1 else ""
        if self.origin_kind and self.origin_kind != self.kind and self.accepted_dir:
            return f"{prefix}{self.origin_kind} → {self.kind}"
        return f"{prefix}{zone_kind}"

    def distance(self, price: float) -> float:
        if price > self.high:
            return price - self.high
        if price < self.low:
            return self.low - price
        return 0.0

    def position(self, price: float) -> str:
        if price > self.high:
            return "OVER"
        if price < self.low:
            return "UNDER"
        return "INSIDE"

    def recent_events(self, now: datetime, max_age_s: float, kinds: tuple = ()) -> list[LevelEvent]:
        return [e for e in self.events if (now - e.ts).total_seconds() <= max_age_s
                and (not kinds or e.event in kinds)]


@dataclass
class LevelMap:
    zones: list[Zone]
    price: float
    nearest_support: Optional[Zone] = None
    nearest_resistance: Optional[Zone] = None
    dist_support: Optional[float] = None
    dist_resistance: Optional[float] = None
    major_level: Optional[Zone] = None
    dist_major: Optional[float] = None
    dist_vwap: Optional[float] = None
    dist_pdh: Optional[float] = None
    dist_pdl: Optional[float] = None
    relations: list[str] = field(default_factory=list)
    unavailable: list[str] = field(default_factory=list)

    def display_zones(self, n: int) -> list[Zone]:
        important = [z for z in self.zones if z.tier <= 2]
        above = sorted((z for z in important if z.low > self.price), key=lambda z: z.low)[:n // 2]
        below = sorted((z for z in important if z.high < self.price), key=lambda z: -z.high)[:n // 2]
        inside = [z for z in important if z.low <= self.price <= z.high]
        return sorted(above + inside + below, key=lambda z: -z.center)


class LevelEngine:
    def __init__(self, cfg: Config, index: str):
        self.cfg = cfg
        self.index = index
        self.c = cfg["levels"]
        self.w = self.c["weights"]
        self.zones: dict[str, Zone] = {}
        self._counter = 0

    # ------------------------------------------------------------ discovery
    def discover(self, price: float, st: StructureState, bars_1m: list[Candle],
                 bars_5m: list[Candle], bars_15m: list[Candle], prev_day: list[Candle],
                 chain: Optional[OptionChain], futures_levels: list[tuple[float, str]],
                 prev_close_feed: Optional[float], now: datetime) -> tuple[list[Candidate], list[str]]:
        w = self.w
        cands: list[Candidate] = []
        unavailable: list[str] = []

        # 1) previous session
        if prev_day:
            day = prev_day[0].ts.date()
            cands += [
                Candidate(max(b.high for b in prev_day), "PDH", f"Prev day high ({day})", "DAILY", w["PDH"]),
                Candidate(min(b.low for b in prev_day), "PDL", f"Prev day low ({day})", "DAILY", w["PDL"]),
                Candidate(prev_day[-1].close, "PDC", "Prev day close", "DAILY", w["PDC"]),
                Candidate(prev_day[0].open, "PDO", "Prev day open", "DAILY", w["PDO"]),
            ]
        elif prev_close_feed:
            cands.append(Candidate(prev_close_feed, "PDC", "Prev close (indicators feed)", "DAILY", w["PDC"]))
            unavailable.append("previous-day high/low (no historical candles in feed)")
        else:
            unavailable.append("previous-day high/low/close (not provided by feeds)")

        done = [b for b in bars_1m if b.complete]
        # 2) current session extremes formed at least 3 bars ago (not the live bar)
        older = done[:-3]
        if older:
            hi = max(older, key=lambda b: b.high)
            lo = min(older, key=lambda b: b.low)
            if hi.high >= max(b.high for b in done):
                cands.append(Candidate(hi.high, "SESSION_HIGH", "Session high", "SESSION", w["SESSION_HIGH"],
                                       hi.ts + timedelta(minutes=1)))
            if lo.low <= min(b.low for b in done):
                cands.append(Candidate(lo.low, "SESSION_LOW", "Session low", "SESSION", w["SESSION_LOW"],
                                       lo.ts + timedelta(minutes=1)))

        # 3) opening range
        if st.or_complete and st.or_high is not None:
            cands.append(Candidate(st.or_high, "OPENING_RANGE_HIGH", "Opening range high", "SESSION",
                                   w["OPENING_RANGE_HIGH"]))
            cands.append(Candidate(st.or_low, "OPENING_RANGE_LOW", "Opening range low", "SESSION",
                                   w["OPENING_RANGE_LOW"]))
        elif not st.or_complete:
            unavailable.append("opening range (incomplete observation of first minutes)")

        # 4) swings on multiple timeframes (each labelled with its source)
        n = self.cfg["structure"]["swing_lookaround"]
        stale = timedelta(minutes=self.c["stale_swing_minutes"])
        for tf, bars, key in (("1m", done, "SWING_1m"),
                              ("5m", [b for b in bars_5m if b.complete], "SWING_5m"),
                              ("15m", [b for b in bars_15m if b.complete], "SWING_15m")):
            if len(bars) < 2 * n + 1:
                continue
            src = bars[-1].source
            gap = self.cfg["structure"]["max_gap_minutes"] * {"1m": 1, "5m": 5, "15m": 15}[tf]
            for s in find_swings_segmented(bars, n, tf, gap):
                wt = w[key] * (w["STALE_SWING_FACTOR"] if now - s.ts > stale else 1.0)
                lab = f"{tf} swing {'high' if s.kind == 'H' else 'low'}"
                if src.startswith("INTERNAL"):
                    lab += " (int.agg)"
                cands.append(Candidate(s.price, "SWING", lab, tf, wt, s.ts))

        # 5) VWAP
        if st.vwap is not None:
            cands.append(Candidate(st.vwap, "VWAP", f"VWAP ({st.vwap_source})", "SESSION", w["VWAP"]))
        else:
            unavailable.append("VWAP (indicator feed not fresh and no volume bars)")

        # 6) option-chain positioning (evidence only, never a guaranteed level)
        if chain is not None:
            cands += self._option_candidates(price, chain)

        # 7) futures-derived levels (already converted to spot-equivalent)
        for px, label in futures_levels:
            cands.append(Candidate(px, "FUTURES", label, "SESSION", w["FUTURES"]))
        if not futures_levels:
            unavailable.append("futures-derived levels (no usable futures OHLC/average price)")

        # 8) round numbers
        steps = self.c["round_number_steps"][self.index]
        rng = price * self.c["round_number_range_pct"] / 100
        k = int((price - rng) // steps["minor"]) + 1
        while k * steps["minor"] <= price + rng:
            px = float(k * steps["minor"])
            major = px % steps["major"] == 0
            cands.append(Candidate(px, "ROUND", f"Round number {px:,.0f}", "STATIC",
                                   w["ROUND_MAJOR"] if major else w["ROUND_MINOR"]))
            k += 1

        # 9) liquidity pools (equal highs / lows)
        if st.ready and st.avg_range:
            for p in find_pools([s for s in st.swings if s.timeframe == "1m"],
                                st.avg_range * self.cfg["liquidity"]["equal_level_ranges"]):
                cands.append(Candidate(p.price, "LIQUIDITY_POOL",
                                       f"Liquidity pool ({p.kind.lower().replace('_', ' ')} x{p.touches})",
                                       "1m", w["LIQUIDITY_POOL"], p.last_ts))

        # 10) supply / demand: base bar before an impulsive bar
        if st.ready and st.avg_range:
            for i in range(1, len(done)):
                b, base = done[i], done[i - 1]
                if (b.ts - base.ts).total_seconds() > 60:
                    continue
                body = abs(b.close - b.open)
                if b.range >= 1.8 * st.avg_range and body >= 0.6 * b.range:
                    kind = "Demand" if b.close > b.open else "Supply"
                    cands.append(Candidate((base.high + base.low) / 2, "SUPPLY_DEMAND",
                                           f"{kind} base before impulse {b.ts:%H:%M}", "1m",
                                           w["SUPPLY_DEMAND"], base.ts, half_width=base.range / 2))
        return cands, unavailable

    def _option_candidates(self, price: float, chain: OptionChain) -> list[Candidate]:
        w = self.w
        out: list[Candidate] = []
        win = price * self.c["oi_window_pct"] / 100
        topn = self.c["oi_top_n"]
        for otype, cat, chg in (("CE", "OI_CE", "OICHG_CE"), ("PE", "OI_PE", "OICHG_PE")):
            qs = [q for (k, t), q in chain.quotes.items() if t == otype and abs(k - price) <= win]
            with_oi = sorted((q for q in qs if q.oi), key=lambda q: -q.oi)[:topn]
            if with_oi:
                mx = with_oi[0].oi
                for rank, q in enumerate(with_oi, 1):
                    out.append(Candidate(q.strike, cat,
                                         f"{otype} OI {q.oi / 1e6:.1f}M (#{rank} near price)", "OPTIONS",
                                         w["OI_CONCENTRATION_MAX"] * q.oi / mx))
            with_chg = sorted((q for q in qs if q.oi_change and q.oi_change > 0),
                              key=lambda q: -q.oi_change)[:topn]
            if with_chg:
                mx = with_chg[0].oi_change
                for rank, q in enumerate(with_chg, 1):
                    out.append(Candidate(q.strike, chg,
                                         f"{otype} OI change +{q.oi_change / 1e6:.1f}M vs prev day (#{rank})",
                                         "OPTIONS", w["OI_CHANGE_MAX"] * q.oi_change / mx))
        a = chain.analytics
        if a is not None:
            for k in a.resistance_strikes:
                if abs(k - price) <= win:
                    out.append(Candidate(k, "SERVER_OI", "Server analytics resistance strike", "OPTIONS",
                                         w["SERVER_OI_LEVEL"]))
            for k in a.support_strikes:
                if abs(k - price) <= win:
                    out.append(Candidate(k, "SERVER_OI", "Server analytics support strike", "OPTIONS",
                                         w["SERVER_OI_LEVEL"]))
            if a.max_pain_strike and abs(a.max_pain_strike - price) <= win:
                out.append(Candidate(a.max_pain_strike, "MAX_PAIN", "Max pain strike", "OPTIONS", w["MAX_PAIN"]))
        return out

    # ----------------------------------------------------------- clustering
    def cluster(self, cands: list[Candidate], price: float) -> list[list[Candidate]]:
        """Single-linkage clustering on sorted prices: a candidate joins the
        current group when it is within ``tol`` of its neighbour and the group
        stays narrower than 2 * tol. Stable when evidence is added or removed."""
        tol = price * self.c["cluster_tolerance_pct"][self.index] / 100
        groups: list[list[Candidate]] = []
        for c in sorted(cands, key=lambda c: c.price):
            if groups and c.price - groups[-1][-1].price <= tol and c.price - groups[-1][0].price <= 2 * tol:
                groups[-1].append(c)
            else:
                groups.append([c])
        return groups

    def _bounds(self, grp: list[Candidate], price: float) -> tuple[float, float, float]:
        lo = min(c.price - c.half_width for c in grp)
        hi = max(c.price + c.half_width for c in grp)
        wts = sum(c.weight for c in grp) or 1.0
        center = sum(c.price * c.weight for c in grp) / wts
        minw = price * self.c["min_zone_width_pct"] / 100
        if hi - lo < minw:
            lo, hi = center - minw / 2, center + minw / 2
        return lo, hi, center

    # -------------------------------------------------------------- scoring
    def score(self, z: Zone) -> None:
        w = self.w
        cat_max: dict[str, float] = {}
        swings = 0
        for c in z.candidates:
            cat_max[c.category] = max(cat_max.get(c.category, 0.0), c.weight)
            if c.category == "SWING":
                swings += 1
        fam: dict[str, float] = {}
        for cat, v in cat_max.items():
            f = FAMILY[cat]
            fam[f] = fam.get(f, 0.0) + v
        fam = {f: min(v, FAMILY_CAP.get(f, 1e9)) for f, v in fam.items()}
        base = sum(fam.values())
        repeated = min(w["REPEATED_REACTION_EACH"] * max(0, swings - 1), w["REPEATED_REACTION_MAX"])
        independent = [f for f in fam if f != "ROUND"]
        conf = min(w["CONFLUENCE_BONUS_EACH"] * max(0, len(independent) - 1), w["CONFLUENCE_BONUS_MAX"])
        rej = min(w["REJECTION_BONUS_EACH"] * z.rejections, w["REJECTION_BONUS_MAX"])
        z.strength = round(min(100.0, base + repeated + conf + rej), 1)
        z.families = sorted(fam)
        if z.strength >= self.c["tier1_min_strength"] or ("PREV_DAY" in fam and len(independent) >= 2):
            z.tier = 1
        elif z.strength >= self.c["tier2_min_strength"] or fam.keys() & {"PREV_DAY", "OPENING_RANGE", "SESSION"}:
            z.tier = 2
        else:
            z.tier = 3
        z.timeframe = max((c.timeframe for c in z.candidates), key=lambda t: TF_RANK.get(t, 0), default="STATIC")

    # --------------------------------------------------------------- update
    def update(self, price: float, now: datetime, cands: list[Candidate], closed_bars: list[Candle],
               avg_range: Optional[float], unavailable: list[str] | None = None,
               vwap: Optional[float] = None) -> LevelMap:
        tol = price * self.c["cluster_tolerance_pct"][self.index] / 100
        rng = avg_range or tol
        matched: set[str] = set()
        for grp in self.cluster(cands, price):
            lo, hi, center = self._bounds(grp, price)
            best = None
            for z in self.zones.values():
                if z.id in matched:
                    continue
                overlap = z.low <= hi + tol / 2 and lo - tol / 2 <= z.high
                d = abs(z.center - center)
                if (overlap or d <= tol) and (best is None or d < abs(best.center - center)):
                    best = z
            if best is None:
                self._counter += 1
                best = Zone(id=f"{self.index}_L_{self._counter:03d}", low=lo, high=hi, center=center)
                best.origin_kind = "RESISTANCE" if center > price else "SUPPORT"
                best.first_seen = now
                best.last_price = price
                best.last_outside = best.position(price) if best.position(price) != "INSIDE" else None
                self.zones[best.id] = best
            best.low, best.high, best.center = lo, hi, center
            best.candidates = grp
            best.last_seen = now
            ts = [c.ts for c in grp if c.ts is not None]
            best.earliest_ts = min(ts) if ts and len(ts) == len(grp) else None
            matched.add(best.id)

        # retain un-rediscovered zones only while their break/reaction story matters
        retain = timedelta(minutes=self.c["retain_minutes"])
        for zid in list(self.zones):
            z = self.zones[zid]
            if zid in matched:
                continue
            active = z.state in BREAK_STATES + TERMINAL + ("TESTING",)
            if not active or (z.last_seen and now - z.last_seen > retain):
                if z.state != "INVALIDATED":
                    z.state = "INVALIDATED"
                    z.events.append(LevelEvent(now, "INVALIDATED", None, price, "evidence no longer present"))
                del self.zones[zid]

        for z in self.zones.values():
            self.score(z)
            self._advance(z, price, now, closed_bars, rng)
            if price > z.high:
                z.kind = "SUPPORT"
            elif price < z.low:
                z.kind = "RESISTANCE"
            else:
                z.kind = z.origin_kind if z.accepted_dir is None else (
                    "SUPPORT" if z.accepted_dir == "UP" else "RESISTANCE")
        return self._map(price, rng, unavailable or [], vwap)

    # --------------------------------------------------------- state machine
    def _set(self, z: Zone, state: str, now: datetime, direction: Optional[str], price: float,
             note: str = "") -> None:
        z.state = state
        z.state_ts = now
        z.events.append(LevelEvent(now, state, direction, price, note))
        if len(z.events) > 50:
            z.events = z.events[-50:]

    def _advance(self, z: Zone, price: float, now: datetime, closed: list[Candle], rng: float) -> None:
        approach = self.c["approach_ranges"] * rng
        react = self.c["reaction_ranges"] * rng
        pos = z.position(price)

        # ---- completed-bar logic for pending breaks
        new_bars = [b for b in closed if z.last_bar_ts is None or b.ts > z.last_bar_ts]
        if z.last_bar_ts is None:
            new_bars = [b for b in new_bars if z.break_ts and b.ts >= z.break_ts.replace(second=0, microsecond=0)]
        for b in new_bars:
            if z.state == "BROKEN":
                up = z.break_dir == "UP"
                beyond = b.close > z.high if up else b.close < z.low
                back = b.close < z.low if up else b.close > z.high
                z.bars_since_break += 1
                if back:
                    self._set(z, "FAILED_BREAKOUT" if up else "FAILED_BREAKDOWN", b.ts + timedelta(minutes=1),
                              "DOWN" if up else "UP", b.close, "closed back through the level")
                    z.break_dir = None
                    z.last_outside = "UNDER" if up else "OVER"
                elif beyond:
                    z.closes_beyond += 1
                    if z.closes_beyond >= self.c["acceptance_closes"]:
                        failed_before = "FAILED_BREAKOUT" if up else "FAILED_BREAKDOWN"
                        reclaimed = ((z.accepted_dir is not None and z.accepted_dir != z.break_dir)
                                     or any(e.event == failed_before for e in z.events))
                        z.accepted_dir = z.break_dir
                        self._set(z, "RECLAIMED" if reclaimed else "ACCEPTED", b.ts + timedelta(minutes=1),
                                  z.break_dir, b.close,
                                  f"{z.closes_beyond} closes {'above' if up else 'below'}")
                else:
                    z.closes_beyond = 0
                    if z.bars_since_break > self.c["failure_window_bars"]:
                        z.entered_from = "UNDER" if up else "OVER"
                        self._set(z, "TESTING", b.ts + timedelta(minutes=1), None, b.close,
                                  "break not accepted; back to testing")
            z.last_bar_ts = b.ts

        # ---- observation logic
        last_out = z.last_outside
        if z.state == "BROKEN":
            up = z.break_dir == "UP"
            z.break_extreme = max(z.break_extreme or price, price) if up else min(z.break_extreme or price, price)
            if (up and price < z.low - react) or (not up and price > z.high + react):
                self._set(z, "FAILED_BREAKOUT" if up else "FAILED_BREAKDOWN", now,
                          "DOWN" if up else "UP", price, "fast rejection back through level")
                z.break_dir = None
            if pos != "INSIDE":
                z.last_outside = pos
        elif pos == "INSIDE":
            if z.state != "TESTING":
                eff = z.pre_approach_state if z.state == "APPROACHING" else z.state
                z.retest_of = z.accepted_dir if eff in ("ACCEPTED", "RECLAIMED") else None
                z.entered_from = last_out
                z.tests += 1
                self._set(z, "TESTING", now, None, price,
                          f"entered from {'below' if last_out == 'UNDER' else 'above' if last_out == 'OVER' else '?'}")
        else:
            # a gap straight through the zone between two consecutive observations
            prev_pos = z.position(z.last_price) if z.last_price is not None else None
            crossed = (prev_pos not in (None, "INSIDE") and prev_pos != pos and z.state != "TESTING")
            if z.state == "TESTING" or crossed:
                ef = z.entered_from if z.state == "TESTING" else last_out
                if crossed:
                    z.tests += 1
                if ef is not None and pos != ef:
                    z.break_dir = "UP" if pos == "OVER" else "DOWN"
                    z.break_ts, z.break_extreme = now, price
                    z.closes_beyond = z.bars_since_break = 0
                    self._set(z, "BROKEN", now, z.break_dir, price,
                              "gap through zone" if crossed else "exited opposite side")
                elif ef is not None and z.distance(price) >= react:
                    z.rejections += 1
                    direction = "DOWN" if pos == "UNDER" else "UP"
                    note = "retest held" if z.retest_of == direction else ""
                    self._set(z, "REJECTED", now, direction, price, note)
                    if note:
                        z.events.append(LevelEvent(now, "RETEST_HELD", direction, price))
                elif ef is None and z.distance(price) >= react:
                    self._set(z, "UNTESTED", now, None, price, "left zone (entry side unknown)")
            elif z.state in ("UNTESTED", "APPROACHING") or (
                    z.state in TERMINAL and z.state_ts and
                    (now - z.state_ts).total_seconds() > self.cfg["setups"]["max_event_age_seconds"]):
                d = z.distance(price)
                moving_closer = z.last_price is not None and z.distance(z.last_price) >= d
                if d <= approach and moving_closer and z.state != "APPROACHING":
                    z.pre_approach_state = z.state
                    self._set(z, "APPROACHING", now, None, price)
                elif d > approach * 1.5 and z.state == "APPROACHING":
                    # revert silently: re-emitting e.g. REJECTED would fake a fresh event
                    z.state, z.state_ts = z.pre_approach_state or "UNTESTED", now
                    z.events.append(LevelEvent(now, "MOVED_AWAY", None, price))
            z.last_outside = pos
        z.last_price = price

    # -------------------------------------------------------------- mapping
    def _map(self, price: float, rng: float, unavailable: list[str], vwap: Optional[float]) -> LevelMap:
        zones = sorted(self.zones.values(), key=lambda z: -z.center)
        lm = LevelMap(zones=zones, price=price, unavailable=unavailable)
        important = [z for z in zones if z.tier <= 2]
        sup = [z for z in important if z.high < price or (z.low <= price <= z.high and z.kind == "SUPPORT")]
        res = [z for z in important if z.low > price or (z.low <= price <= z.high and z.kind == "RESISTANCE")]
        if sup:
            lm.nearest_support = max(sup, key=lambda z: z.high)
            lm.dist_support = price - lm.nearest_support.high
        if res:
            lm.nearest_resistance = min(res, key=lambda z: z.low)
            lm.dist_resistance = lm.nearest_resistance.low - price
        near_major = [z for z in zones if z.tier == 1]
        if near_major:
            lm.major_level = min(near_major, key=lambda z: z.distance(price))
            lm.dist_major = lm.major_level.center - price
        if vwap is not None:
            lm.dist_vwap = price - vwap
        for z in zones:
            cats = {c.category for c in z.candidates}
            if "PDH" in cats:
                lm.dist_pdh = price - z.center
            if "PDL" in cats:
                lm.dist_pdl = price - z.center
        lm.relations = self._relations(important, price)
        return lm

    @staticmethod
    def _relations(zones: list[Zone], price: float) -> list[str]:
        out = []
        for z in sorted(zones, key=lambda z: z.distance(price))[:4]:
            k = z.kind
            s = z.state
            tag = f"{z.center:,.0f} ({z.id})"
            if s == "APPROACHING":
                out.append(f"APPROACHING {k} {tag}")
            elif s == "TESTING":
                if z.retest_of:
                    out.append(f"RETESTING {z.origin_kind or k} {tag} after acceptance {z.retest_of}")
                else:
                    out.append(f"AT {k} {tag}")
            elif s == "REJECTED":
                last = next((e for e in reversed(z.events) if e.event == "REJECTED"), None)
                if last and last.direction == "UP":
                    out.append(f"BOUNCING FROM SUPPORT {tag}")
                elif last:
                    out.append(f"REJECTING RESISTANCE {tag}")
            elif s == "BROKEN":
                out.append(f"{'BREAKING RESISTANCE' if z.break_dir == 'UP' else 'BREAKING SUPPORT'} {tag}"
                           " — awaiting acceptance")
            elif s in ("ACCEPTED", "RECLAIMED"):
                out.append(f"{s} {'ABOVE' if z.accepted_dir == 'UP' else 'BELOW'} {tag}")
            elif s in ("FAILED_BREAKOUT", "FAILED_BREAKDOWN"):
                out.append(f"{s} at {tag}")
        return out

"""Normalized data models.

These are the ONLY shapes the analytical modules see. Raw JSON is mapped into
them by ``schema_adapter`` using field names observed in the live samples
(samples/schema/20260924_103510). ``None`` always means "not available" —
never a substituted value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawResponse:
    index: str
    feed: str                  # spot | options | depth | indicators | futures
    url: str
    fetched_at: datetime       # local clock, IST
    http_status: Optional[int]
    elapsed_ms: Optional[float]
    body: Optional[bytes]
    payload: Optional[dict]
    error: Optional[str]       # network error or JSON error
    server_date: Optional[datetime] = None   # HTTP Date header


@dataclass
class Candle:
    ts: datetime               # bar START time, IST
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    source: str                # e.g. FEED_1m, INTERNAL_AGG_1m, INTERNAL_AGG_5m, FEED_5m
    complete: bool = True
    observations: int = 0      # internal bars: number of raw price observations

    @property
    def range(self) -> float:
        return self.high - self.low


@dataclass
class SpotData:
    symbol: str
    session_status: Optional[str]
    session_date: Optional[str]
    server_time: Optional[datetime]
    feed_status: Optional[str]
    feed_messages: Optional[float]
    feed_last_error: Optional[str]
    last_tick_epoch: Optional[float]
    ltp: Optional[float]
    ltp_ts: Optional[datetime]
    candles: dict[str, list[Candle]]
    candle_source: dict[str, str]
    synthetic: Optional[bool]


@dataclass
class OptionQuote:
    strike: float
    option_type: str           # CE | PE
    security_id: Optional[int]
    ltp: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    bid_qty: Optional[float]
    ask_qty: Optional[float]
    volume: Optional[float]
    oi: Optional[float]
    prev_oi: Optional[float]
    prev_close: Optional[float]
    prev_volume: Optional[float]
    avg_price: Optional[float]
    iv: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]

    @property
    def oi_change(self) -> Optional[float]:
        if self.oi is None or self.prev_oi is None:
            return None
        return self.oi - self.prev_oi

    @property
    def spread(self) -> Optional[float]:
        if self.bid is None or self.ask is None:
            return None
        return self.ask - self.bid

    @property
    def mid(self) -> Optional[float]:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2

    @property
    def spread_pct(self) -> Optional[float]:
        m = self.mid
        s = self.spread
        if m is None or s is None or m <= 0:
            return None
        return s / m * 100

    @property
    def quote_valid(self) -> bool:
        return (self.ltp is not None and self.bid is not None and self.ask is not None
                and self.ask >= self.bid)


@dataclass
class ChainAnalytics:
    pcr_oi: Optional[float]
    pcr_volume: Optional[float]
    atm_strike: Optional[float]
    max_pain_strike: Optional[float]
    resistance_strikes: list[float]
    support_strikes: list[float]
    total_call_oi: Optional[float]
    total_put_oi: Optional[float]
    total_call_volume: Optional[float]
    total_put_volume: Optional[float]
    avg_call_iv: Optional[float]
    avg_put_iv: Optional[float]
    iv_skew: Optional[float]
    oi_change_class: dict[tuple[float, str], str]
    crossed_markets_detected: Optional[float]
    duplicate_security_ids: Optional[float]


@dataclass
class OptionChain:
    symbol: str
    status: Optional[str]
    market_status: Optional[str]
    market_open: Optional[bool]
    underlying_ltp: Optional[float]
    expiry: Optional[str]
    expiry_list: list[str]
    updated_at: Optional[datetime]
    fetch_count: Optional[float]
    synthetic: Optional[bool]
    quotes: dict[tuple[float, str], OptionQuote]
    strikes: list[float]
    analytics: Optional[ChainAnalytics]
    malformed_records: int = 0

    def quote(self, strike: float, option_type: str) -> Optional[OptionQuote]:
        return self.quotes.get((float(strike), option_type))


@dataclass
class DepthLevel:
    level: int
    price: float
    quantity: float
    orders: Optional[float]


@dataclass
class DepthContract:
    security_id: Optional[str]
    strike: float
    option_type: str
    expiry: Optional[str]
    bids: list[DepthLevel]
    asks: list[DepthLevel]
    ltp: Optional[float]
    avg_price: Optional[float]
    buy_qty: Optional[float]
    sell_qty: Optional[float]
    volume: Optional[float]
    oi: Optional[float]
    quote_updated_at: Optional[datetime]
    updated_at: Optional[datetime]
    crossed_book: Optional[bool]


@dataclass
class DepthData:
    symbol: str
    status: Optional[str]
    market_status: Optional[str]
    market_open: Optional[bool]
    underlying_ltp: Optional[float]
    expiry: Optional[str]
    depth_levels: Optional[int]
    contracts: list[DepthContract]
    updated_at: Optional[datetime]
    packet_count: Optional[float]
    synthetic: Optional[bool]
    error: Optional[str]


@dataclass
class FuturesData:
    symbol: str
    status: Optional[str]
    market_status: Optional[str]
    market_open: Optional[bool]
    trading_symbol: Optional[str]
    expiry: Optional[str]
    last_price: Optional[float]
    ohlc: Optional[dict[str, float]]
    volume: Optional[float]
    oi: Optional[float]
    oi_change: Optional[float]
    average_price: Optional[float]
    buy_qty: Optional[float]
    sell_qty: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    updated_at: Optional[datetime]
    synthetic: Optional[bool]
    error: Optional[str]


@dataclass
class IndicatorData:
    symbol: str
    status: Optional[str]
    timeframe: Optional[str]
    as_of: Optional[datetime]           # START of the latest bar
    bar_count: Optional[float]
    last_price: Optional[float]
    previous_close: Optional[float]
    today_open: Optional[float]
    values: dict[str, float]            # only indicators flagged ready AND non-null
    not_ready: list[str]
    server_freshness: Optional[str]
    synthetic: Optional[bool]


@dataclass
class FeedCheck:
    feed: str
    state: str                          # OK | DEGRADED | BLOCKED
    reasons: list[str] = field(default_factory=list)
    http_status: Optional[int] = None
    age_seconds: Optional[float] = None

    @property
    def usable(self) -> bool:
        return self.state in ("OK", "DEGRADED")


@dataclass
class IndexSnapshot:
    """Everything the analytical layer needs for one index in one cycle."""
    index: str
    ref_time: datetime
    spot: Optional[SpotData]
    chain: Optional[OptionChain]
    depth: Optional[DepthData]
    futures: Optional[FuturesData]
    indicators: Optional[IndicatorData]
    adapter_issues: dict[str, list[str]] = field(default_factory=dict)

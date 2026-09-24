# Live endpoint schema, as observed

Source: `samples/raw/20260924_103510` (3 rounds, 20 s apart, 2026-09-24 10:35 IST),
captured by `tools/inspect_endpoints.py` on the user's machine. The full machine-generated report is
`samples/schema/20260924_103510/schema_report.md`. Everything below was **observed**. When a
field was only ever `null` in the samples, this document says so.

All 15 endpoints returned parseable JSON objects. **HTTP 503 was returned together with a
structured JSON body**, so the engine judges each feed by its payload and timestamps, never by
the status code alone.

| endpoint | HTTP | payload status | verdict at capture time |
|---|---|---|---|
| nifty / banknifty / sensex | 200 | `session.status=LIVE`, `feed.status=CONNECTED` | `ltp=null`, `feed.messages=0`; candles stop at 09:15–09:17 → **not a live price source** |
| *-options | 200 | `status=LIVE`, `market_status=OPEN` | `updated_at` ~10 s old, refreshes every ~3 s → **usable (primary)** |
| nifty-depth, banknifty-depth | 200 | `status=LIVE` | 20-level books, `updated_at` fresh → **usable** |
| sensex-depth | 503 | `status=ERROR`, `error=WebSocketConnectionClosedException…` | ladders empty, but per-contract `quote_updated_at`, `buy_quantity`, `sell_quantity` fresh → **degraded (quote-only)** |
| *-futures | 503 | `status=ERROR`, `error=RuntimeError: DHAN_<IDX>_FUTURES_NOT_RESOLVED` | every price field `null` → **blocked** |
| nifty-indicators | 503 | `status=STARTING` | no `result` → **blocked** |
| banknifty/sensex-indicators | 200 | `status=OK`, `result.freshness.status=FRESH` | `result.as_of` = 09:16 / 09:17 while fetched at 10:35 → **stale; the server's FRESH flag is contradicted by its own `as_of`** |

## Spot index — `<idx>.json` (`schema_version` "3.0")

```
service, schema_version, symbol ("NIFTY"), security_id ("13"), exchange_segment ("IDX_I"), instrument ("INDEX")
session: {status "LIVE", date "2026-09-24", timezone "Asia/Kolkata", current_time_ist "2026-09-24 10:35:10 IST"}
feed:    {status "CONNECTED", messages 0, quote_packets 0, last_error "", last_tick_received_epoch null}
ltp: null            ltp_timestamp: null          (never populated in the samples)
timeframes: ["1m","5m","15m","1h"]
candle_source: {"1m": "DHAN_WEBSOCKET_FULL", "5m"/"15m"/"1h": "DHAN_HISTORICAL_API"}
synthetic_candles: false
"1m" | "5m" | "15m" | "1h": [ {timestamp "2026-09-24 09:15:00 IST", open, high, low, close, volume}, … ]
```
Only `1m` had rows (0–3). `5m`/`15m`/`1h` were empty, so previous-day levels are not available.

## Option chain — `<idx>-options.json`

```
service, symbol, status "LIVE", market_status "OPEN", market_open true, data_source "DHAN_OPTION_CHAIN_API",
security_id, exchange_segment, instrument, underlying_ltp 23228.6, expiry "2026-09-29", expiry_list [18 dates],
updated_at "2026-09-24T10:34:58.610102+05:30", fetch_count, synthetic_data false, storage, refresh_seconds 3.2
strikes: [ {strike 23250.0,
            ce: {average_price, greeks{delta, theta, gamma, vega}, implied_volatility, last_price, oi,
                 previous_close_price, previous_oi, previous_volume, security_id (int),
                 top_ask_price, top_ask_quantity, top_bid_price, top_bid_quantity, volume},
            pe: {same keys} } ]           (268 strikes NIFTY; step 50 NIFTY, 100 BANKNIFTY/SENSEX near ATM)
analytics: {pcr_oi, pcr_volume, atm_strike, max_pain_strike, resistance_strikes[3], support_strikes[3],
            total_call_oi, total_put_oi, total_call_volume, total_put_volume, avg_call_iv, avg_put_iv, iv_skew,
            contracts: [{security_id, strike, option_type "CE"/"PE", moneyness "ITM"/"OTM", oi, volume,
                         last_price, implied_volatility, oi_change_classification}],
            data_quality: {contracts_total, contracts_missing_security_id, duplicate_security_ids,
                           crossed_markets_detected}}
```
* CE/PE are represented as the `ce` / `pe` sub-objects of each strike row.
* **0 is a placeholder for "no data".** On every untraded strike, `last_price`, bid/ask, IV and
  greeks are all 0 together. The adapter turns 0 into `None` for prices, IV and greeks. OI and
  volume keep a real 0.
* There is no OI-change field. It is **derived** as `oi - previous_oi` (versus the previous
  day). Intraday OI and volume changes are derived by the engine from its own polls.
* `oi_change_classification` values observed: LONG_UNWINDING, SHORT_BUILDUP, SHORT_COVERING, LONG_BUILDUP.

## Depth — `<idx>-depth.json`

```
service, symbol, status "LIVE"|"ERROR", market_status, market_open, data_source "DHAN_FULL_MARKET_DEPTH_WEBSOCKET",
underlying_security_id, exchange_segment "NSE_FNO"/"BSE_FNO", instrument "OPTIDX", depth_levels 20,
underlying_ltp, expiry, contract_count 50,
contracts: [{security_id (str), strike, option_type, expiry,
             bid: [{level 1..20, price, quantity, orders}], ask: [...],
             last_price, average_price, buy_quantity, sell_quantity, volume, oi,
             ohlc {open, high, low, close}, quote_updated_at, updated_at (absent when ERROR), crossed_book}],
updated_at (null when ERROR), connection_count, packet_count, synthetic_data, storage, quote_refresh_seconds,
error (only when ERROR)
```
Coverage is 25 strikes × CE/PE around ATM.

## Futures — `<idx>-futures.json`

```
service, symbol, status "ERROR", market_status "OPEN", market_open true, data_source "DHAN_MARKET_QUOTE_API",
security_id, exchange_segment, instrument, trading_symbol, expiry, lot_size, tick_size, last_price, ohlc,
volume, oi, oi_change, average_price, buy_quantity, sell_quantity, top_bid_price, top_ask_price,
raw_quote {}, updated_at, fetch_count 0, synthetic_data, storage, refresh_seconds, error
```
**Every value field was `null`** (status ERROR, `DHAN_<IDX>_FUTURES_NOT_RESOLVED`). The adapter
reads these fields by name and discards any value whose type doesn't match. The feed is
accepted only when `status` is in `integrity.accepted_feed_status.futures` (default
`LIVE`/`OK`, fail-closed). If it reports another value, add that value in `config.json`.

## Indicators — `<idx>-indicators.json`

```
service "PSYGRID_MASTER_INDICATOR", engine_version, symbol, status "OK"|"STARTING", timeframe "1m", sync_count,
result: {symbol, security_id, previous_close, today_open, timeframe, synthetic_candles, bar_count,
         as_of "2026-09-24T09:16:00+05:30", freshness {status, age_seconds, reason}, last_price,
         price_change_from_previous_close_pct, price_change_from_today_open_pct,
         latest_bar {timestamp, open, high, low, close, volume},
         indicators {sma_20, ema_9, ema_20, vwap, vwma_20, bb_*, true_range, atr_14, natr_14, rsi_14, macd_line,
                     macd_signal, macd_histogram, stoch_*, cci_20, roc_12, momentum_10, williams_r_14, adx_14,
                     plus_di_14, minus_di_14, obv, cmf_20, mfi_14, rvol_20, donchian_*, keltner_*, supertrend,
                     supertrend_direction},
         indicator_status {<name>: {ready, valid_observations, required_observations}}}
```
`result` is absent while the status is STARTING. The engine uses an indicator only when
`indicator_status[name].ready` is true and its value is non-null. `supertrend_direction` was
never populated, so its encoding is unknown and it is not used.

## Timestamps and freshness

| feed | field | format |
|---|---|---|
| spot | `session.current_time_ist`, candle `timestamp` | `YYYY-MM-DD HH:MM:SS IST` |
| options / depth / futures | `updated_at`, `quote_updated_at` | ISO-8601 with `+05:30` |
| indicators | `result.as_of` (bar **start**), `latest_bar.timestamp` | ISO-8601 with `+05:30` |
| all | HTTP `Date` header | RFC 1123 GMT (used to correct local clock drift) |

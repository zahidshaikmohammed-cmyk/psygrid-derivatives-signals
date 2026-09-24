# PSYGRID live endpoint schema report

Run: `20260924_103510` — generated 2026-09-24 10:35:52 IST

Every path below was observed in real responses. `present` counts how many
parent objects contained the key. Timestamp hints are heuristics and must be
verified by a human before the schema adapter relies on them.

## Fetch summary

| endpoint | HTTP | ms | bytes | JSON | top-level | error |
|---|---|---|---|---|---|---|
| nifty | 200 | 47.0 | 611 | ok | dict | "" |
| nifty-options | 200 | 31.0 | 288088 | ok | dict | "" |
| nifty-depth | 200 | 47.0 | 126170 | ok | dict | "" |
| nifty-indicators | 503 | 31.0 | 118 | ok | dict | "" |
| nifty-futures | 503 | 15.0 | 612 | ok | dict | "" |
| banknifty | 200 | 16.0 | 854 | ok | dict | "" |
| banknifty-options | 200 | 63.0 | 383903 | ok | dict | "" |
| banknifty-depth | 200 | 46.0 | 124381 | ok | dict | "" |
| banknifty-indicators | 200 | 16.0 | 4452 | ok | dict | "" |
| banknifty-futures | 503 | 15.0 | 620 | ok | dict | "" |
| sensex | 200 | 16.0 | 970 | ok | dict | "" |
| sensex-options | 200 | 47.0 | 215441 | ok | dict | "" |
| sensex-depth | 503 | 15.0 | 18153 | ok | dict | "" |
| sensex-indicators | 200 | 16.0 | 4445 | ok | dict | "" |
| sensex-futures | 503 | 0.0 | 614 | ok | dict | "" |

## nifty

- URL: `http://140.245.226.102:10000/public/nifty.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:50 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.schema_version` | {"str": 3} | 3/3 | ["3.0"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["NIFTY"] |  |  |  |  |  |  |  |
| `$.security_id` | {"str": 3} | 3/3 | ["13"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["IDX_I"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["INDEX"] |  |  |  |  |  |  |  |
| `$.session` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.session.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.session.date` | {"str": 3} | 3/3 | ["2026-09-24"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.session.timezone` | {"str": 3} | 3/3 | ["Asia/Kolkata"] |  |  |  |  |  | name looks time-related |  |
| `$.session.current_time_ist` | {"str": 3} | 3/3 | ["2026-09-24 10:35:10 IST", "2026-09-24 10:35:31 IST", "2026-09-24 10:35:51 IST"] |  |  |  |  |  | name looks time-related | 2 |
| `$.feed` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.feed.status` | {"str": 3} | 3/3 | ["CONNECTED"] |  |  |  |  |  |  |  |
| `$.feed.messages` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.feed.quote_packets` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.feed.last_error` | {"str": 3} | 3/3 | [""] |  |  |  |  |  |  |  |
| `$.feed.last_tick_received_epoch` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ltp` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ltp_timestamp` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.timeframes` | {"list": 3} | 3/3 | [] |  |  |  |  | [4, 4] | name looks time-related |  |
| `$.timeframes[]` | {"str": 12} | 12/12 | ["1m", "5m", "15m"] |  |  |  |  |  | name looks time-related |  |
| `$.candle_source` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.candle_source.1m` | {"str": 3} | 3/3 | ["DHAN_WEBSOCKET_FULL"] |  |  |  |  |  |  |  |
| `$.candle_source.5m` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.candle_source.15m` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.candle_source.1h` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.synthetic_candles` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.1m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.1m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.5m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.5m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.15m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.15m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.1h` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.1h[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |

## nifty-options

- URL: `http://140.245.226.102:10000/public/nifty-options.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:50 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["NIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_OPTION_CHAIN_API"] |  |  |  |  |  |  |  |
| `$.security_id` | {"str": 3} | 3/3 | ["13"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["IDX_I"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["INDEX"] |  |  |  |  |  |  |  |
| `$.underlying_ltp` | {"float": 3} | 3/3 | [23228.6, 23226.4, 23221.05] | 23221.05 | 23228.6 |  |  |  |  | 2 |
| `$.expiry` | {"str": 3} | 3/3 | ["2026-09-29"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.expiry_list` | {"list": 3} | 3/3 | [] |  |  |  |  | [18, 18] |  |  |
| `$.expiry_list[]` | {"str": 54} | 54/54 | ["2026-09-29", "2026-10-06", "2026-10-13"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [268, 268] |  |  |
| `$.strikes[]` | {"dict": 804} | 804/804 | [] |  |  |  |  |  |  |  |
| `$.strikes[].strike` | {"float": 804} | 804/804 | [1500.0, 3000.0, 4500.0] | 1500.0 | 49500.0 |  |  |  |  |  |
| `$.strikes[].ce` | {"dict": 804} | 804/804 | [] |  |  |  |  |  |  |  |
| `$.strikes[].ce.average_price` | {"int": 486, "float": 318} | 804/804 | [0, 3743.28, 2240.65] | 0 | 3743.28 | 480 |  |  |  | 26 |
| `$.strikes[].ce.greeks` | {"dict": 804} | 804/804 | [] |  |  |  |  |  |  |  |
| `$.strikes[].ce.greeks.delta` | {"int": 519, "float": 285} | 804/804 | [0, 0.70084, 0.69436] | 0 | 0.99487 | 519 |  |  |  | 61 |
| `$.strikes[].ce.greeks.theta` | {"int": 519, "float": 285} | 804/804 | [0, -152.93, -151.84961] | -153.43343 | 0 | 519 |  |  |  | 68 |
| `$.strikes[].ce.greeks.gamma` | {"int": 535, "float": 269} | 804/804 | [0, 7e-05, 8e-05] | 0 | 0.00154 | 535 |  |  |  | 30 |
| `$.strikes[].ce.greeks.vega` | {"int": 519, "float": 285} | 804/804 | [0, 9.84817, 9.94236] | 0 | 11.30591 | 519 |  |  |  | 66 |
| `$.strikes[].ce.implied_volatility` | {"int": 327, "float": 477} | 804/804 | [0, 164.93394062099208, 162.2088296016792] | 0 | 165.3530144666548 | 327 |  |  |  | 72 |
| `$.strikes[].ce.last_price` | {"int": 479, "float": 325} | 804/804 | [0, 10499.3, 10168.85] | 0 | 10499.3 | 420 |  |  |  | 47 |
| `$.strikes[].ce.oi` | {"int": 804} | 804/804 | [0, 780, 115895] | 0 | 18715125 | 435 |  |  |  | 27 |
| `$.strikes[].ce.previous_close_price` | {"int": 474, "float": 330} | 804/804 | [0, 10499.3, 10168.85] | 0 | 10499.3 | 420 |  |  |  |  |
| `$.strikes[].ce.previous_oi` | {"int": 804} | 804/804 | [0, 780, 116090] | 0 | 15299505 | 438 |  |  |  |  |
| `$.strikes[].ce.previous_volume` | {"int": 804} | 804/804 | [0, 65, 14365] | 0 | 200613010 | 435 |  |  |  |  |
| `$.strikes[].ce.security_id` | {"int": 804} | 804/804 | [43870, 55254, 55258] | 35084 | 74583 |  |  |  |  |  |
| `$.strikes[].ce.top_ask_price` | {"int": 449, "float": 355} | 804/804 | [0, 8772.15, 7199.6] | 0 | 8772.15 | 420 |  |  |  | 79 |
| `$.strikes[].ce.top_ask_quantity` | {"int": 804} | 804/804 | [0, 1690, 780] | 0 | 317330 | 420 |  |  |  | 64 |
| `$.strikes[].ce.top_bid_price` | {"int": 434, "float": 370} | 804/804 | [0, 7527.55, 6208.95] | 0 | 7527.95 | 420 |  |  |  | 80 |
| `$.strikes[].ce.top_bid_quantity` | {"int": 804} | 804/804 | [0, 1690, 780] | 0 | 508950 | 420 |  |  |  | 77 |
| `$.strikes[].ce.volume` | {"int": 804} | 804/804 | [0, 390, 10790] | 0 | 45812520 | 480 |  |  |  | 64 |
| `$.strikes[].pe` | {"dict": 804} | 804/804 | [] |  |  |  |  |  |  |  |
| `$.strikes[].pe.average_price` | {"int": 543, "float": 261} | 804/804 | [0, 0.43, 0.42] | 0 | 6777.56 | 537 |  |  |  | 26 |
| `$.strikes[].pe.greeks` | {"dict": 804} | 804/804 | [] |  |  |  |  |  |  |  |
| `$.strikes[].pe.greeks.delta` | {"int": 504, "float": 300} | 804/804 | [0, -0.00076, -0.00179] | -0.98386 | 0 | 504 |  |  |  | 94 |
| `$.strikes[].pe.greeks.theta` | {"int": 504, "float": 300} | 804/804 | [0, -0.4515, -0.73818] | -25.2452 | 3.28869 | 504 |  |  |  | 101 |
| `$.strikes[].pe.greeks.gamma` | {"int": 510, "float": 294} | 804/804 | [0, 1e-05, 2e-05] | 0 | 0.00133 | 510 |  |  |  | 38 |
| `$.strikes[].pe.greeks.vega` | {"int": 504, "float": 300} | 804/804 | [0, 0.07405, 0.16285] | 0 | 11.30644 | 504 |  |  |  | 100 |
| `$.strikes[].pe.implied_volatility` | {"int": 279, "float": 525} | 804/804 | [0, 49.95549532948401, 42.49888650347125] | 0 | 80.1733254171388 | 279 |  |  |  | 278 |
| `$.strikes[].pe.last_price` | {"int": 505, "float": 299} | 804/804 | [0, 0.45, 0.4] | 0 | 7064.95 | 420 |  |  |  | 75 |
| `$.strikes[].pe.oi` | {"int": 804} | 804/804 | [0, 108095, 136760] | 0 | 11496030 | 471 |  |  |  | 46 |
| `$.strikes[].pe.previous_close_price` | {"int": 498, "float": 306} | 804/804 | [0, 0.4, 0.45] | 0 | 7064.95 | 420 |  |  |  |  |
| `$.strikes[].pe.previous_oi` | {"int": 804} | 804/804 | [0, 102440, 133445] | 0 | 12675765 | 471 |  |  |  |  |
| `$.strikes[].pe.previous_volume` | {"int": 804} | 804/804 | [0, 126035, 129220] | 0 | 231890620 | 471 |  |  |  |  |
| `$.strikes[].pe.security_id` | {"int": 804} | 804/804 | [43871, 55255, 55261] | 35085 | 74584 |  |  |  |  |  |
| `$.strikes[].pe.top_ask_price` | {"int": 435, "float": 369} | 804/804 | [0, 0.45, 0.5] | 0 | 11926.95 | 420 |  |  |  | 81 |
| `$.strikes[].pe.top_ask_quantity` | {"int": 804} | 804/804 | [0, 5785, 6370] | 0 | 120770 | 420 |  |  |  | 107 |
| `$.strikes[].pe.top_bid_price` | {"int": 454, "float": 350} | 804/804 | [0, 0.4, 0.45] | 0 | 10482.1 | 420 |  |  |  | 82 |
| `$.strikes[].pe.top_bid_quantity` | {"int": 804} | 804/804 | [0, 4290, 4485] | 0 | 105820 | 420 |  |  |  | 108 |
| `$.strikes[].pe.volume` | {"int": 804} | 804/804 | [0, 42510, 42965] | 0 | 71988800 | 537 |  |  |  | 100 |
| `$.updated_at` | {"str": 3} | 3/3 | ["2026-09-24T10:34:58.610102+05:30", "2026-09-24T10:35:16.310988+05:30", "2026-09-24T10:35:36.568671+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.fetch_count` | {"int": 3} | 3/3 | [17626, 17627, 17628] | 17626 | 17628 |  |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.refresh_seconds` | {"float": 3} | 3/3 | [3.2] | 3.2 | 3.2 |  |  |  |  |  |
| `$.analytics` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.analytics.pcr_oi` | {"float": 3} | 3/3 | [0.7581038360205709, 0.75798344627151, 0.7604485946854088] | 0.75798344627151 | 0.7604485946854088 |  |  |  |  |  |
| `$.analytics.pcr_volume` | {"float": 3} | 3/3 | [1.0121294980012785, 1.0122863058585259, 1.0132240132573818] | 1.0121294980012785 | 1.0132240132573818 |  |  |  |  |  |
| `$.analytics.atm_strike` | {"float": 3} | 3/3 | [23250.0, 23200.0] | 23200.0 | 23250.0 |  |  |  |  |  |
| `$.analytics.max_pain_strike` | {"float": 3} | 3/3 | [23400.0] | 23400.0 | 23400.0 |  |  |  |  |  |
| `$.analytics.resistance_strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.analytics.resistance_strikes[]` | {"float": 9} | 9/9 | [24000.0, 23500.0, 23400.0] | 23400.0 | 24000.0 |  |  |  |  |  |
| `$.analytics.support_strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.analytics.support_strikes[]` | {"float": 9} | 9/9 | [23000.0, 23200.0, 23300.0] | 23000.0 | 23300.0 |  |  |  |  |  |
| `$.analytics.total_call_oi` | {"float": 3} | 3/3 | [227722710.0, 227759565.0, 227634440.0] | 227634440.0 | 227759565.0 |  |  |  |  |  |
| `$.analytics.total_put_oi` | {"float": 3} | 3/3 | [172637460.0, 172637980.0, 173104290.0] | 172637460.0 | 173104290.0 |  |  |  |  |  |
| `$.analytics.total_call_volume` | {"float": 3} | 3/3 | [518413870.0, 519151165.0, 520102700.0] | 518413870.0 | 520102700.0 |  |  |  |  |  |
| `$.analytics.total_put_volume` | {"float": 3} | 3/3 | [524701970.0, 525529615.0, 526980545.0] | 524701970.0 | 526980545.0 |  |  |  |  |  |
| `$.analytics.avg_call_iv` | {"float": 3} | 3/3 | [11.921175412465841, 11.908190589061292, 11.937844703579845] | 11.908190589061292 | 11.937844703579845 |  |  |  |  |  |
| `$.analytics.avg_put_iv` | {"float": 3} | 3/3 | [12.214782362236434, 12.232234885078292, 12.221739504702915] | 12.214782362236434 | 12.232234885078292 |  |  |  |  |  |
| `$.analytics.iv_skew` | {"float": 3} | 3/3 | [-0.2936069497705933, -0.324044296017, -0.2838948011230702] | -0.324044296017 | -0.2838948011230702 |  |  |  |  |  |
| `$.analytics.contracts` | {"list": 3} | 3/3 | [] |  |  |  |  | [536, 536] |  |  |
| `$.analytics.contracts[]` | {"dict": 1608} | 1608/1608 | [] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].security_id` | {"int": 1608} | 1608/1608 | [43870, 43871, 55254] | 35084 | 74584 |  |  |  |  |  |
| `$.analytics.contracts[].strike` | {"float": 1608} | 1608/1608 | [1500.0, 3000.0, 4500.0] | 1500.0 | 49500.0 |  |  |  |  |  |
| `$.analytics.contracts[].option_type` | {"str": 1608} | 1608/1608 | ["CE", "PE"] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].moneyness` | {"str": 1608} | 1608/1608 | ["ITM", "OTM"] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].oi` | {"float": 1608} | 1608/1608 | [0.0, 108095.0, 136760.0] | 0.0 | 18715125.0 | 906 |  |  |  |  |
| `$.analytics.contracts[].volume` | {"float": 1608} | 1608/1608 | [0.0, 42510.0, 42965.0] | 0.0 | 71988800.0 | 1017 |  |  |  |  |
| `$.analytics.contracts[].last_price` | {"float": 1608} | 1608/1608 | [0.0, 10499.3, 0.45] | 0.0 | 10499.3 | 840 |  |  |  |  |
| `$.analytics.contracts[].implied_volatility` | {"float": 1608} | 1608/1608 | [0.0, 49.95549532948401, 42.49888650347125] | 0.0 | 165.3530144666548 | 606 |  |  |  |  |
| `$.analytics.contracts[].oi_change_classification` | {"str": 1608} | 1608/1608 | ["LONG_UNWINDING", "LONG_BUILDUP", "SHORT_BUILDUP"] |  |  |  |  |  |  |  |
| `$.analytics.data_quality` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.analytics.data_quality.contracts_total` | {"int": 3} | 3/3 | [536] | 536 | 536 |  |  |  |  |  |
| `$.analytics.data_quality.contracts_missing_security_id` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.analytics.data_quality.duplicate_security_ids` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.analytics.data_quality.crossed_markets_detected` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |

## nifty-depth

- URL: `http://140.245.226.102:10000/public/nifty-depth.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:50 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["NIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_FULL_MARKET_DEPTH_WEBSOCKET"] |  |  |  |  |  |  |  |
| `$.underlying_security_id` | {"str": 3} | 3/3 | ["13"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["NSE_FNO"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["OPTIDX"] |  |  |  |  |  |  |  |
| `$.depth_levels` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.underlying_ltp` | {"float": 3} | 3/3 | [23227.1, 23228.6, 23226.4] | 23226.4 | 23228.6 |  |  |  |  | 2 |
| `$.expiry` | {"str": 3} | 3/3 | ["2026-09-29"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.contract_count` | {"int": 3} | 3/3 | [50] | 50 | 50 |  |  |  |  |  |
| `$.contracts` | {"list": 3} | 3/3 | [] |  |  |  |  | [50, 50] |  |  |
| `$.contracts[]` | {"dict": 150} | 150/150 | [] |  |  |  |  |  |  |  |
| `$.contracts[].security_id` | {"str": 150} | 150/150 | ["73887", "73888", "73889"] |  |  |  |  |  |  |  |
| `$.contracts[].strike` | {"float": 150} | 150/150 | [22600.0, 22650.0, 22700.0] | 22600.0 | 23800.0 |  |  |  |  |  |
| `$.contracts[].option_type` | {"str": 150} | 150/150 | ["CE", "PE"] |  |  |  |  |  |  |  |
| `$.contracts[].expiry` | {"str": 150} | 150/150 | ["2026-09-29"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.contracts[].bid` | {"list": 150} | 150/150 | [] |  |  |  |  | [20, 20] |  |  |
| `$.contracts[].bid[]` | {"dict": 3000} | 3000/3000 | [] |  |  |  |  |  |  |  |
| `$.contracts[].bid[].level` | {"int": 3000} | 3000/3000 | [1, 2, 3] | 1 | 20 |  |  |  |  |  |
| `$.contracts[].bid[].price` | {"float": 3000} | 3000/3000 | [649.65, 649.6, 648.9] | 5.15 | 649.65 |  |  |  |  | 1090 |
| `$.contracts[].bid[].quantity` | {"int": 3000} | 3000/3000 | [65, 130, 260] | 65 | 50960 |  |  |  |  | 1003 |
| `$.contracts[].bid[].orders` | {"int": 3000} | 3000/3000 | [1, 3, 2] | 1 | 117 |  |  |  |  | 781 |
| `$.contracts[].ask` | {"list": 150} | 150/150 | [] |  |  |  |  | [20, 20] |  |  |
| `$.contracts[].ask[]` | {"dict": 3000} | 3000/3000 | [] |  |  |  |  |  |  |  |
| `$.contracts[].ask[].level` | {"int": 3000} | 3000/3000 | [1, 2, 3] | 1 | 20 |  |  |  |  |  |
| `$.contracts[].ask[].price` | {"float": 3000} | 3000/3000 | [652.65, 652.7, 652.75] | 6.15 | 677.35 |  |  |  |  | 1056 |
| `$.contracts[].ask[].quantity` | {"int": 3000} | 3000/3000 | [65, 195, 260] | 65 | 50505 |  |  |  |  | 938 |
| `$.contracts[].ask[].orders` | {"int": 3000} | 3000/3000 | [1, 2, 4] | 1 | 69 |  |  |  |  | 728 |
| `$.contracts[].last_price` | {"int": 17, "float": 133} | 150/150 | [634, 6.45, 606.9] | 6.15 | 634 |  |  |  |  | 48 |
| `$.contracts[].average_price` | {"float": 150} | 150/150 | [660.04, 6.38, 600.55] | 5.82 | 660.04 |  |  |  |  | 24 |
| `$.contracts[].buy_quantity` | {"int": 150} | 150/150 | [23205, 2241005, 20995] | 20150 | 3392675 |  |  |  |  | 52 |
| `$.contracts[].sell_quantity` | {"int": 150} | 150/150 | [14495, 476970, 12610] | 12610 | 1702610 |  |  |  |  | 52 |
| `$.contracts[].volume` | {"int": 150} | 150/150 | [7605, 12336480, 3380] | 3380 | 72125495 |  |  |  |  | 48 |
| `$.contracts[].oi` | {"int": 150} | 150/150 | [9360, 2964585, 44785] | 9360 | 13503620 |  |  |  |  | 23 |
| `$.contracts[].ohlc` | {"dict": 150} | 150/150 | [] |  |  |  |  |  |  |  |
| `$.contracts[].ohlc.open` | {"float": 99, "int": 51} | 150/150 | [695.05, 5.9, 620.05] | 5.9 | 695.05 |  |  |  |  |  |
| `$.contracts[].ohlc.close` | {"float": 147, "int": 3} | 150/150 | [854.55, 4.6, 795.55] | 4.6 | 854.55 |  |  |  |  |  |
| `$.contracts[].ohlc.high` | {"float": 129, "int": 21} | 150/150 | [695.05, 8.7, 634.2] | 7.6 | 695.05 |  |  |  |  |  |
| `$.contracts[].ohlc.low` | {"float": 120, "int": 30} | 150/150 | [626.25, 5.1, 583.3] | 4.7 | 626.25 |  |  |  |  |  |
| `$.contracts[].quote_updated_at` | {"str": 150} | 150/150 | ["2026-09-24T10:33:39.324921+05:30", "2026-09-24T10:33:39.324926+05:30", "2026-09-24T10:35:01.280890+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 | 52 |
| `$.contracts[].updated_at` | {"str": 150} | 150/150 | ["2026-09-24T10:35:10.373907+05:30", "2026-09-24T10:35:10.373918+05:30", "2026-09-24T10:35:10.373849+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 | 56 |
| `$.contracts[].crossed_book` | {"bool": 150} | 150/150 | [false] |  |  |  |  |  |  |  |
| `$.updated_at` | {"str": 3} | 3/3 | ["2026-09-24T10:35:10.373918+05:30", "2026-09-24T10:35:31.156137+05:30", "2026-09-24T10:35:51.559447+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.connection_count` | {"int": 3} | 3/3 | [572] | 572 | 572 |  |  |  |  |  |
| `$.packet_count` | {"int": 3} | 3/3 | [21096320, 21105214, 21114094] | 21096320 | 21114094 |  |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.quote_refresh_seconds` | {"float": 3} | 3/3 | [1.0] | 1.0 | 1.0 |  |  |  |  |  |

## nifty-indicators

- URL: `http://140.245.226.102:10000/public/nifty-indicators.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:50 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID_MASTER_INDICATOR"] |  |  |  |  |  |  |  |
| `$.engine_version` | {"str": 3} | 3/3 | ["1.0.0"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["NIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["STARTING"] |  |  |  |  |  |  |  |
| `$.timeframe` | {"str": 3} | 3/3 | ["1m"] |  |  |  |  |  | name looks time-related |  |

## nifty-futures

- URL: `http://140.245.226.102:10000/public/nifty-futures.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:50 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["NIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["ERROR"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_MARKET_QUOTE_API"] |  |  |  |  |  |  |  |
| `$.security_id` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.exchange_segment` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.instrument` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.trading_symbol` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.expiry` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.lot_size` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.tick_size` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.last_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ohlc` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.volume` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.oi` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.oi_change` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.average_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.buy_quantity` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.sell_quantity` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.top_bid_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.top_ask_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.raw_quote` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.updated_at` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.fetch_count` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.refresh_seconds` | {"float": 3} | 3/3 | [2.0] | 2.0 | 2.0 |  |  |  |  |  |
| `$.error` | {"str": 3} | 3/3 | ["RuntimeError: DHAN_NIFTY_FUTURES_NOT_RESOLVED"] |  |  |  |  |  |  |  |

## banknifty

- URL: `http://140.245.226.102:10000/public/banknifty.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:50 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.schema_version` | {"str": 3} | 3/3 | ["3.0"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["BANKNIFTY"] |  |  |  |  |  |  |  |
| `$.security_id` | {"str": 3} | 3/3 | ["25"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["IDX_I"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["INDEX"] |  |  |  |  |  |  |  |
| `$.session` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.session.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.session.date` | {"str": 3} | 3/3 | ["2026-09-24"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.session.timezone` | {"str": 3} | 3/3 | ["Asia/Kolkata"] |  |  |  |  |  | name looks time-related |  |
| `$.session.current_time_ist` | {"str": 3} | 3/3 | ["2026-09-24 10:35:10 IST", "2026-09-24 10:35:31 IST", "2026-09-24 10:35:51 IST"] |  |  |  |  |  | name looks time-related | 2 |
| `$.feed` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.feed.status` | {"str": 3} | 3/3 | ["CONNECTED"] |  |  |  |  |  |  |  |
| `$.feed.messages` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.feed.quote_packets` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.feed.last_error` | {"str": 3} | 3/3 | [""] |  |  |  |  |  |  |  |
| `$.feed.last_tick_received_epoch` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ltp` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ltp_timestamp` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.timeframes` | {"list": 3} | 3/3 | [] |  |  |  |  | [4, 4] | name looks time-related |  |
| `$.timeframes[]` | {"str": 12} | 12/12 | ["1m", "5m", "15m"] |  |  |  |  |  | name looks time-related |  |
| `$.candle_source` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.candle_source.1m` | {"str": 3} | 3/3 | ["DHAN_WEBSOCKET_FULL"] |  |  |  |  |  |  |  |
| `$.candle_source.5m` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.candle_source.15m` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.candle_source.1h` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.synthetic_candles` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.1m` | {"list": 3} | 3/3 | [] |  |  |  |  | [2, 2] |  |  |
| `$.1m[]` | {"dict": 6} | 6/6 | [] |  |  |  |  |  |  |  |
| `$.1m[].timestamp` | {"str": 6} | 6/6 | ["2026-09-24 09:15:00 IST", "2026-09-24 09:16:00 IST"] |  |  |  |  |  | name looks time-related |  |
| `$.1m[].open` | {"float": 6} | 6/6 | [55710.6, 55865.4] | 55710.6 | 55865.4 |  |  |  |  |  |
| `$.1m[].high` | {"float": 6} | 6/6 | [55918.4, 55877.05] | 55877.05 | 55918.4 |  |  |  |  |  |
| `$.1m[].low` | {"float": 6} | 6/6 | [55621.45, 55789.15] | 55621.45 | 55789.15 |  |  |  |  |  |
| `$.1m[].close` | {"float": 6} | 6/6 | [55870.15, 55792.95] | 55792.95 | 55870.15 |  |  |  |  |  |
| `$.1m[].volume` | {"int": 6} | 6/6 | [10960584, 7587188] | 7587188 | 10960584 |  |  |  |  |  |
| `$.5m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.5m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.15m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.15m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.1h` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.1h[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |

## banknifty-options

- URL: `http://140.245.226.102:10000/public/banknifty-options.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["BANKNIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_OPTION_CHAIN_API"] |  |  |  |  |  |  |  |
| `$.security_id` | {"str": 3} | 3/3 | ["25"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["IDX_I"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["INDEX"] |  |  |  |  |  |  |  |
| `$.underlying_ltp` | {"float": 3} | 3/3 | [55575.5, 55574.2, 55568.35] | 55568.35 | 55575.5 |  |  |  |  | 2 |
| `$.expiry` | {"str": 3} | 3/3 | ["2026-09-29"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.expiry_list` | {"list": 3} | 3/3 | [] |  |  |  |  | [6, 6] |  |  |
| `$.expiry_list[]` | {"str": 18} | 18/18 | ["2026-09-29", "2026-10-27", "2026-11-23"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [364, 364] |  |  |
| `$.strikes[]` | {"dict": 1092} | 1092/1092 | [] |  |  |  |  |  |  |  |
| `$.strikes[].strike` | {"float": 1092} | 1092/1092 | [28500.0, 30000.0, 31500.0] | 28500.0 | 84000.0 |  |  |  |  |  |
| `$.strikes[].ce` | {"dict": 1092} | 1092/1092 | [] |  |  |  |  |  |  |  |
| `$.strikes[].ce.average_price` | {"int": 829, "float": 263} | 1092/1092 | [0, 10840.64, 7814.92] | 0 | 10840.64 | 819 |  |  |  | 2 |
| `$.strikes[].ce.greeks` | {"dict": 1092} | 1092/1092 | [] |  |  |  |  |  |  |  |
| `$.strikes[].ce.greeks.delta` | {"int": 654, "float": 438} | 1092/1092 | [0, 0.98059, 0.9491] | 0 | 0.98059 | 654 |  |  |  | 44 |
| `$.strikes[].ce.greeks.theta` | {"int": 654, "float": 438} | 1092/1092 | [0, -37.50602, -62.18689] | -457.08884 | 0 | 654 |  |  |  | 48 |
| `$.strikes[].ce.greeks.gamma` | {"int": 711, "float": 381} | 1092/1092 | [0, 1e-05, 2e-05] | 0 | 0.00042 | 711 |  |  |  |  |
| `$.strikes[].ce.greeks.vega` | {"int": 654, "float": 438} | 1092/1092 | [0, 3.213, 7.10083] | 0 | 27.05638 | 654 |  |  |  | 48 |
| `$.strikes[].ce.implied_volatility` | {"int": 342, "float": 750} | 1092/1092 | [0, 86.7247382219825, 76.42017505160497] | 0 | 221.79468958744616 | 342 |  |  |  | 60 |
| `$.strikes[].ce.last_price` | {"int": 721, "float": 371} | 1092/1092 | [0, 13878.45, 10741.65] | 0 | 13878.45 | 642 |  |  |  | 2 |
| `$.strikes[].ce.oi` | {"int": 1092} | 1092/1092 | [0, 20940, 30] | 0 | 2000310 | 756 |  |  |  | 1 |
| `$.strikes[].ce.previous_close_price` | {"int": 723, "float": 369} | 1092/1092 | [0, 13878.45, 11660.5] | 0 | 13878.45 | 642 |  |  |  |  |
| `$.strikes[].ce.previous_oi` | {"int": 1092} | 1092/1092 | [0, 20970, 30] | 0 | 1970520 | 759 |  |  |  |  |
| `$.strikes[].ce.previous_volume` | {"int": 1092} | 1092/1092 | [0, 480, 60] | 0 | 7097340 | 759 |  |  |  |  |
| `$.strikes[].ce.security_id` | {"int": 1092} | 1092/1092 | [65461, 65463, 59189] | 35000 | 70643 |  |  |  |  |  |
| `$.strikes[].ce.top_ask_price` | {"int": 660, "float": 432} | 1092/1092 | [0, 13258.55, 10774.8] | 0 | 13258.55 | 642 |  |  |  | 61 |
| `$.strikes[].ce.top_ask_quantity` | {"int": 1092} | 1092/1092 | [0, 300, 30] | 0 | 7290 | 642 |  |  |  | 6 |
| `$.strikes[].ce.top_bid_price` | {"int": 671, "float": 421} | 1092/1092 | [0, 11120.05, 10680.85] | 0 | 11123.75 | 642 |  |  |  | 37 |
| `$.strikes[].ce.top_bid_quantity` | {"int": 1092} | 1092/1092 | [0, 300, 30] | 0 | 1560 | 642 |  |  |  | 4 |
| `$.strikes[].ce.volume` | {"int": 1092} | 1092/1092 | [0, 150, 240] | 0 | 2949450 | 819 |  |  |  | 2 |
| `$.strikes[].pe` | {"dict": 1092} | 1092/1092 | [] |  |  |  |  |  |  |  |
| `$.strikes[].pe.average_price` | {"int": 823, "float": 269} | 1092/1092 | [0, 0.23, 0.27] | 0 | 10263.54 | 810 |  |  |  | 1 |
| `$.strikes[].pe.greeks` | {"dict": 1092} | 1092/1092 | [] |  |  |  |  |  |  |  |
| `$.strikes[].pe.greeks.delta` | {"int": 870, "float": 222} | 1092/1092 | [0, -0.0002, -0.00033] | -0.98976 | 0 | 870 |  |  |  | 16 |
| `$.strikes[].pe.greeks.theta` | {"int": 870, "float": 222} | 1092/1092 | [0, -0.27082, -0.38223] | -62.14503 | 13.30967 | 870 |  |  |  | 22 |
| `$.strikes[].pe.greeks.gamma` | {"int": 900, "float": 192} | 1092/1092 | [0, 1e-05, 2e-05] | 0 | 0.00055 | 900 |  |  |  |  |
| `$.strikes[].pe.greeks.vega` | {"int": 870, "float": 222} | 1092/1092 | [0, 0.05169, 0.08161] | 0 | 27.03583 | 870 |  |  |  | 20 |
| `$.strikes[].pe.implied_volatility` | {"float": 552, "int": 540} | 1092/1092 | [17.666201868407164, 16.34807304612708, 15.092893139545765] | 0 | 69.7912931512388 | 540 |  |  |  | 284 |
| `$.strikes[].pe.last_price` | {"int": 734, "float": 358} | 1092/1092 | [0, 0.2, 0.3] | 0 | 12300 | 642 |  |  |  | 14 |
| `$.strikes[].pe.oi` | {"int": 1092} | 1092/1092 | [0, 156570, 171000] | 0 | 1277160 | 738 |  |  |  | 10 |
| `$.strikes[].pe.previous_close_price` | {"int": 711, "float": 381} | 1092/1092 | [0, 0.25, 0.85] | 0 | 12300 | 642 |  |  |  |  |
| `$.strikes[].pe.previous_oi` | {"int": 1092} | 1092/1092 | [0, 156570, 171030] | 0 | 1314750 | 738 |  |  |  |  |
| `$.strikes[].pe.previous_volume` | {"int": 1092} | 1092/1092 | [0, 42060, 19590] | 0 | 7021800 | 738 |  |  |  |  |
| `$.strikes[].pe.security_id` | {"int": 1092} | 1092/1092 | [65462, 65464, 59190] | 35001 | 70644 |  |  |  |  |  |
| `$.strikes[].pe.top_ask_price` | {"int": 669, "float": 423} | 1092/1092 | [0, 0.25, 0.3] | 0 | 13602.3 | 642 |  |  |  | 21 |
| `$.strikes[].pe.top_ask_quantity` | {"int": 1092} | 1092/1092 | [0, 10980, 3810] | 0 | 10980 | 642 |  |  |  | 25 |
| `$.strikes[].pe.top_bid_price` | {"int": 675, "float": 417} | 1092/1092 | [0, 0.2, 0.25] | 0 | 11822.3 | 642 |  |  |  | 20 |
| `$.strikes[].pe.top_bid_quantity` | {"int": 1092} | 1092/1092 | [0, 1740, 240] | 0 | 1740 | 642 |  |  |  | 27 |
| `$.strikes[].pe.volume` | {"int": 1092} | 1092/1092 | [0, 6990, 24810] | 0 | 2961270 | 810 |  |  |  | 18 |
| `$.updated_at` | {"str": 3} | 3/3 | ["2026-09-24T10:34:51.997759+05:30", "2026-09-24T10:35:26.640805+05:30", "2026-09-24T10:35:44.742177+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.fetch_count` | {"int": 3} | 3/3 | [17755, 17756, 17757] | 17755 | 17757 |  |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.refresh_seconds` | {"float": 3} | 3/3 | [3.2] | 3.2 | 3.2 |  |  |  |  |  |
| `$.analytics` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.analytics.pcr_oi` | {"float": 3} | 3/3 | [0.7676746819146238, 0.7674527537067397, 0.7674906070245049] | 0.7674527537067397 | 0.7676746819146238 |  |  |  |  |  |
| `$.analytics.pcr_volume` | {"float": 3} | 3/3 | [0.9687645278790531, 0.9686116857398104, 0.9687740485982133] | 0.9686116857398104 | 0.9687740485982133 |  |  |  |  |  |
| `$.analytics.atm_strike` | {"float": 3} | 3/3 | [55600.0] | 55600.0 | 55600.0 |  |  |  |  |  |
| `$.analytics.max_pain_strike` | {"float": 3} | 3/3 | [56500.0] | 56500.0 | 56500.0 |  |  |  |  |  |
| `$.analytics.resistance_strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.analytics.resistance_strikes[]` | {"float": 9} | 9/9 | [57500.0, 58000.0, 57000.0] | 57000.0 | 58000.0 |  |  |  |  |  |
| `$.analytics.support_strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.analytics.support_strikes[]` | {"float": 9} | 9/9 | [57500.0, 54000.0, 56000.0] | 54000.0 | 57500.0 |  |  |  |  |  |
| `$.analytics.total_call_oi` | {"float": 3} | 3/3 | [21647490.0, 21647730.0, 21654480.0] | 21647490.0 | 21654480.0 |  |  |  |  |  |
| `$.analytics.total_put_oi` | {"float": 3} | 3/3 | [16618230.0, 16613610.0, 16619610.0] | 16613610.0 | 16619610.0 |  |  |  |  |  |
| `$.analytics.total_call_volume` | {"float": 3} | 3/3 | [35233980.0, 35327160.0, 35358090.0] | 35233980.0 | 35358090.0 |  |  |  |  |  |
| `$.analytics.total_put_volume` | {"float": 3} | 3/3 | [34133430.0, 34218300.0, 34254000.0] | 34133430.0 | 34254000.0 |  |  |  |  |  |
| `$.analytics.avg_call_iv` | {"float": 3} | 3/3 | [26.27452424073586, 26.264639952754475, 26.29276163476496] | 26.264639952754475 | 26.29276163476496 |  |  |  |  |  |
| `$.analytics.avg_put_iv` | {"float": 3} | 3/3 | [6.674542821498738, 6.6737090482533485, 6.669913998286528] | 6.669913998286528 | 6.674542821498738 |  |  |  |  |  |
| `$.analytics.iv_skew` | {"float": 3} | 3/3 | [19.599981419237125, 19.59093090450113, 19.622847636478433] | 19.59093090450113 | 19.622847636478433 |  |  |  |  |  |
| `$.analytics.contracts` | {"list": 3} | 3/3 | [] |  |  |  |  | [728, 728] |  |  |
| `$.analytics.contracts[]` | {"dict": 2184} | 2184/2184 | [] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].security_id` | {"int": 2184} | 2184/2184 | [65461, 65462, 65463] | 35000 | 70644 |  |  |  |  |  |
| `$.analytics.contracts[].strike` | {"float": 2184} | 2184/2184 | [28500.0, 30000.0, 31500.0] | 28500.0 | 84000.0 |  |  |  |  |  |
| `$.analytics.contracts[].option_type` | {"str": 2184} | 2184/2184 | ["CE", "PE"] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].moneyness` | {"str": 2184} | 2184/2184 | ["ITM", "OTM"] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].oi` | {"float": 2184} | 2184/2184 | [0.0, 156570.0, 20940.0] | 0.0 | 2000310.0 | 1494 |  |  |  |  |
| `$.analytics.contracts[].volume` | {"float": 2184} | 2184/2184 | [0.0, 6990.0, 150.0] | 0.0 | 2961270.0 | 1629 |  |  |  |  |
| `$.analytics.contracts[].last_price` | {"float": 2184} | 2184/2184 | [0.0, 13878.45, 0.2] | 0.0 | 13878.45 | 1284 |  |  |  |  |
| `$.analytics.contracts[].implied_volatility` | {"float": 2184} | 2184/2184 | [0.0, 17.666201868407164, 16.34807304612708] | 0.0 | 221.79468958744616 | 882 |  |  |  |  |
| `$.analytics.contracts[].oi_change_classification` | {"str": 2184} | 2184/2184 | ["LONG_UNWINDING", "SHORT_BUILDUP", "SHORT_COVERING"] |  |  |  |  |  |  |  |
| `$.analytics.data_quality` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.analytics.data_quality.contracts_total` | {"int": 3} | 3/3 | [728] | 728 | 728 |  |  |  |  |  |
| `$.analytics.data_quality.contracts_missing_security_id` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.analytics.data_quality.duplicate_security_ids` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.analytics.data_quality.crossed_markets_detected` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |

## banknifty-depth

- URL: `http://140.245.226.102:10000/public/banknifty-depth.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["BANKNIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_FULL_MARKET_DEPTH_WEBSOCKET"] |  |  |  |  |  |  |  |
| `$.underlying_security_id` | {"str": 3} | 3/3 | ["25"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["NSE_FNO"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["OPTIDX"] |  |  |  |  |  |  |  |
| `$.depth_levels` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.underlying_ltp` | {"float": 3} | 3/3 | [55579.7, 55575.5, 55574.2] | 55574.2 | 55579.7 |  |  |  |  | 2 |
| `$.expiry` | {"str": 3} | 3/3 | ["2026-09-29"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.contract_count` | {"int": 3} | 3/3 | [50] | 50 | 50 |  |  |  |  |  |
| `$.contracts` | {"list": 3} | 3/3 | [] |  |  |  |  | [50, 50] |  |  |
| `$.contracts[]` | {"dict": 150} | 150/150 | [] |  |  |  |  |  |  |  |
| `$.contracts[].security_id` | {"str": 150} | 150/150 | ["69708", "69709", "69710"] |  |  |  |  |  |  |  |
| `$.contracts[].strike` | {"float": 150} | 150/150 | [54300.0, 54400.0, 54500.0] | 54300.0 | 56700.0 |  |  |  |  |  |
| `$.contracts[].option_type` | {"str": 150} | 150/150 | ["CE", "PE"] |  |  |  |  |  |  |  |
| `$.contracts[].expiry` | {"str": 150} | 150/150 | ["2026-09-29"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.contracts[].bid` | {"list": 150} | 150/150 | [] |  |  |  |  | [20, 20] |  |  |
| `$.contracts[].bid[]` | {"dict": 3000} | 3000/3000 | [] |  |  |  |  |  |  |  |
| `$.contracts[].bid[].level` | {"int": 3000} | 3000/3000 | [1, 2, 3] | 1 | 20 |  |  |  |  |  |
| `$.contracts[].bid[].price` | {"float": 3000} | 3000/3000 | [1359.85, 1359.8, 1359.4] | 0.0 | 1440.45 | 59 |  |  |  | 1058 |
| `$.contracts[].bid[].quantity` | {"int": 3000} | 3000/3000 | [300, 120, 30] | 0 | 6300 | 59 |  |  |  | 665 |
| `$.contracts[].bid[].orders` | {"int": 3000} | 3000/3000 | [1, 0, 3] | 0 | 20 | 59 |  |  |  | 444 |
| `$.contracts[].ask` | {"list": 150} | 150/150 | [] |  |  |  |  | [20, 20] |  |  |
| `$.contracts[].ask[]` | {"dict": 3000} | 3000/3000 | [] |  |  |  |  |  |  |  |
| `$.contracts[].ask[].level` | {"int": 3000} | 3000/3000 | [1, 2, 3] | 1 | 20 |  |  |  |  |  |
| `$.contracts[].ask[].price` | {"float": 3000} | 3000/3000 | [1581.2, 1581.25, 1581.65] | 0.0 | 1733.05 | 63 |  |  |  | 1057 |
| `$.contracts[].ask[].quantity` | {"int": 3000} | 3000/3000 | [300, 120, 30] | 0 | 1470 | 63 |  |  |  | 734 |
| `$.contracts[].ask[].orders` | {"int": 3000} | 3000/3000 | [1, 0, 2] | 0 | 8 | 63 |  |  |  | 393 |
| `$.contracts[].last_price` | {"int": 34, "float": 116} | 150/150 | [2100, 35.2, 1392.9] | 35.2 | 2100 |  |  |  |  | 39 |
| `$.contracts[].average_price` | {"int": 5, "float": 145} | 150/150 | [0, 29.45, 1397.18] | 0 | 1397.18 | 3 |  |  |  | 30 |
| `$.contracts[].buy_quantity` | {"int": 150} | 150/150 | [3210, 21690, 3360] | 3210 | 622230 |  |  |  |  | 51 |
| `$.contracts[].sell_quantity` | {"int": 150} | 150/150 | [3150, 16320, 3300] | 3150 | 198930 |  |  |  |  | 48 |
| `$.contracts[].volume` | {"int": 150} | 150/150 | [0, 287220, 120] | 0 | 2960250 | 3 |  |  |  | 39 |
| `$.contracts[].oi` | {"int": 150} | 150/150 | [210, 84480, 540] | 210 | 1209840 |  |  |  |  | 18 |
| `$.contracts[].ohlc` | {"dict": 150} | 150/150 | [] |  |  |  |  |  |  |  |
| `$.contracts[].ohlc.open` | {"int": 63, "float": 87} | 150/150 | [0, 20.25, 1404.1] | 0 | 1454.4 | 3 |  |  |  |  |
| `$.contracts[].ohlc.close` | {"int": 6, "float": 144} | 150/150 | [2100, 8.05, 2320.9] | 8.05 | 2320.9 |  |  |  |  |  |
| `$.contracts[].ohlc.high` | {"int": 18, "float": 132} | 150/150 | [0, 48.25, 1409.5] | 0 | 1454.4 | 3 |  |  |  |  |
| `$.contracts[].ohlc.low` | {"int": 24, "float": 126} | 150/150 | [0, 18.15, 1382.25] | 0 | 1382.25 | 3 |  |  |  |  |
| `$.contracts[].quote_updated_at` | {"str": 150} | 150/150 | ["2026-09-24T10:31:24.891681+05:30", "2026-09-24T10:31:24.891686+05:30", "2026-09-24T10:35:00.230757+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 | 52 |
| `$.contracts[].updated_at` | {"str": 150} | 150/150 | ["2026-09-24T10:35:10.570386+05:30", "2026-09-24T10:35:10.570400+05:30", "2026-09-24T10:35:10.570330+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 | 56 |
| `$.contracts[].crossed_book` | {"bool": 150} | 150/150 | [false] |  |  |  |  |  |  |  |
| `$.updated_at` | {"str": 3} | 3/3 | ["2026-09-24T10:35:10.570400+05:30", "2026-09-24T10:35:31.170081+05:30", "2026-09-24T10:35:51.962396+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.connection_count` | {"int": 3} | 3/3 | [527] | 527 | 527 |  |  |  |  |  |
| `$.packet_count` | {"int": 3} | 3/3 | [30803490, 30812120, 30820782] | 30803490 | 30820782 |  |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.quote_refresh_seconds` | {"float": 3} | 3/3 | [1.0] | 1.0 | 1.0 |  |  |  |  |  |

## banknifty-indicators

- URL: `http://140.245.226.102:10000/public/banknifty-indicators.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID_MASTER_INDICATOR"] |  |  |  |  |  |  |  |
| `$.engine_version` | {"str": 3} | 3/3 | ["1.0.0"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["BANKNIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["OK"] |  |  |  |  |  |  |  |
| `$.timeframe` | {"str": 3} | 3/3 | ["1m"] |  |  |  |  |  | name looks time-related |  |
| `$.sync_count` | {"int": 3} | 3/3 | [4] | 4 | 4 |  |  |  |  |  |
| `$.result` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.symbol` | {"str": 3} | 3/3 | ["BANKNIFTY"] |  |  |  |  |  |  |  |
| `$.result.security_id` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.previous_close` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.today_open` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.timeframe` | {"str": 3} | 3/3 | ["1m"] |  |  |  |  |  | name looks time-related |  |
| `$.result.synthetic_candles` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.bar_count` | {"int": 3} | 3/3 | [2] | 2 | 2 |  |  |  |  |  |
| `$.result.as_of` | {"str": 3} | 3/3 | ["2026-09-24T09:16:00+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.result.freshness` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.freshness.status` | {"str": 3} | 3/3 | ["FRESH"] |  |  |  |  |  |  |  |
| `$.result.freshness.age_seconds` | {"float": 3} | 3/3 | [89.0] | 89.0 | 89.0 |  |  |  |  |  |
| `$.result.freshness.reason` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.last_price` | {"float": 3} | 3/3 | [55792.95] | 55792.95 | 55792.95 |  |  |  |  |  |
| `$.result.price_change_from_previous_close_pct` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.price_change_from_today_open_pct` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.latest_bar` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.latest_bar.timestamp` | {"str": 3} | 3/3 | ["2026-09-24T09:16:00+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.result.latest_bar.open` | {"float": 3} | 3/3 | [55865.4] | 55865.4 | 55865.4 |  |  |  |  |  |
| `$.result.latest_bar.high` | {"float": 3} | 3/3 | [55877.05] | 55877.05 | 55877.05 |  |  |  |  |  |
| `$.result.latest_bar.low` | {"float": 3} | 3/3 | [55789.15] | 55789.15 | 55789.15 |  |  |  |  |  |
| `$.result.latest_bar.close` | {"float": 3} | 3/3 | [55792.95] | 55792.95 | 55792.95 |  |  |  |  |  |
| `$.result.latest_bar.volume` | {"float": 3} | 3/3 | [7587188.0] | 7587188.0 | 7587188.0 |  |  |  |  |  |
| `$.result.indicators` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicators.sma_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.ema_9` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.ema_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.vwap` | {"float": 3} | 3/3 | [55810.03513180631] | 55810.03513180631 | 55810.03513180631 |  |  |  |  |  |
| `$.result.indicators.vwma_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_middle_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_upper_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_lower_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_width_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_percent_b_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.true_range` | {"float": 3} | 3/3 | [87.90000000000146] | 87.90000000000146 | 87.90000000000146 |  |  |  |  |  |
| `$.result.indicators.atr_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.natr_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.rsi_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.macd_line` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.macd_signal` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.macd_histogram` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.stoch_raw_k` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.stoch_k` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.stoch_d` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.cci_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.roc_12` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.momentum_10` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.williams_r_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.adx_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.plus_di_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.minus_di_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.obv` | {"float": 3} | 3/3 | [-7587188.0] | -7587188.0 | -7587188.0 |  |  |  |  |  |
| `$.result.indicators.cmf_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.mfi_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.rvol_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.donchian_upper_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.donchian_lower_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.donchian_middle_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.keltner_middle` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.keltner_upper` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.keltner_lower` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.supertrend` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.supertrend_direction` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicator_status` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.sma_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.sma_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.sma_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.sma_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.ema_9` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_9.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_9.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.ema_9.required_observations` | {"int": 3} | 3/3 | [9] | 9 | 9 |  |  |  |  |  |
| `$.result.indicator_status.ema_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.ema_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.vwap` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwap.ready` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwap.valid_observations` | {"int": 3} | 3/3 | [2] | 2 | 2 |  |  |  |  |  |
| `$.result.indicator_status.vwap.required_observations` | {"int": 3} | 3/3 | [1] | 1 | 1 |  |  |  |  |  |
| `$.result.indicator_status.vwma_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwma_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwma_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.vwma_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_middle_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_middle_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_middle_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_middle_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_upper_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_upper_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_upper_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_upper_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_lower_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_lower_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_lower_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_lower_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_width_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_width_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_width_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_width_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.true_range` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.true_range.ready` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.result.indicator_status.true_range.valid_observations` | {"int": 3} | 3/3 | [2] | 2 | 2 |  |  |  |  |  |
| `$.result.indicator_status.true_range.required_observations` | {"int": 3} | 3/3 | [1] | 1 | 1 |  |  |  |  |  |
| `$.result.indicator_status.atr_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.atr_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.atr_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.atr_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.natr_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.natr_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.natr_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.natr_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.rsi_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rsi_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rsi_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.rsi_14.required_observations` | {"int": 3} | 3/3 | [15] | 15 | 15 |  |  |  |  |  |
| `$.result.indicator_status.macd_line` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_line.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_line.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.macd_line.required_observations` | {"int": 3} | 3/3 | [26] | 26 | 26 |  |  |  |  |  |
| `$.result.indicator_status.macd_signal` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_signal.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_signal.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.macd_signal.required_observations` | {"int": 3} | 3/3 | [34] | 34 | 34 |  |  |  |  |  |
| `$.result.indicator_status.macd_histogram` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_histogram.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_histogram.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.macd_histogram.required_observations` | {"int": 3} | 3/3 | [34] | 34 | 34 |  |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.stoch_k` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_k.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_k.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.stoch_k.required_observations` | {"int": 3} | 3/3 | [16] | 16 | 16 |  |  |  |  |  |
| `$.result.indicator_status.stoch_d` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_d.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_d.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.stoch_d.required_observations` | {"int": 3} | 3/3 | [18] | 18 | 18 |  |  |  |  |  |
| `$.result.indicator_status.cci_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cci_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cci_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.cci_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.roc_12` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.roc_12.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.roc_12.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.roc_12.required_observations` | {"int": 3} | 3/3 | [13] | 13 | 13 |  |  |  |  |  |
| `$.result.indicator_status.momentum_10` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.momentum_10.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.momentum_10.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.momentum_10.required_observations` | {"int": 3} | 3/3 | [11] | 11 | 11 |  |  |  |  |  |
| `$.result.indicator_status.williams_r_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.williams_r_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.williams_r_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.williams_r_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.adx_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.adx_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.adx_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.adx_14.required_observations` | {"int": 3} | 3/3 | [27] | 27 | 27 |  |  |  |  |  |
| `$.result.indicator_status.plus_di_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.plus_di_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.plus_di_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.plus_di_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.minus_di_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.minus_di_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.minus_di_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.minus_di_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.obv` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.obv.ready` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.result.indicator_status.obv.valid_observations` | {"int": 3} | 3/3 | [2] | 2 | 2 |  |  |  |  |  |
| `$.result.indicator_status.obv.required_observations` | {"int": 3} | 3/3 | [1] | 1 | 1 |  |  |  |  |  |
| `$.result.indicator_status.cmf_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cmf_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cmf_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.cmf_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.mfi_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.mfi_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.mfi_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.mfi_14.required_observations` | {"int": 3} | 3/3 | [15] | 15 | 15 |  |  |  |  |  |
| `$.result.indicator_status.rvol_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rvol_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rvol_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.rvol_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.keltner_middle` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_middle.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_middle.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.keltner_middle.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.keltner_upper` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_upper.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_upper.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.keltner_upper.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.keltner_lower` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_lower.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_lower.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.keltner_lower.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.supertrend` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.supertrend.required_observations` | {"int": 3} | 3/3 | [10] | 10 | 10 |  |  |  |  |  |
| `$.result.indicator_status.supertrend_direction` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend_direction.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend_direction.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.supertrend_direction.required_observations` | {"int": 3} | 3/3 | [10] | 10 | 10 |  |  |  |  |  |

## banknifty-futures

- URL: `http://140.245.226.102:10000/public/banknifty-futures.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["BANKNIFTY"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["ERROR"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_MARKET_QUOTE_API"] |  |  |  |  |  |  |  |
| `$.security_id` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.exchange_segment` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.instrument` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.trading_symbol` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.expiry` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.lot_size` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.tick_size` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.last_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ohlc` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.volume` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.oi` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.oi_change` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.average_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.buy_quantity` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.sell_quantity` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.top_bid_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.top_ask_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.raw_quote` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.updated_at` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.fetch_count` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.refresh_seconds` | {"float": 3} | 3/3 | [2.0] | 2.0 | 2.0 |  |  |  |  |  |
| `$.error` | {"str": 3} | 3/3 | ["RuntimeError: DHAN_BANKNIFTY_FUTURES_NOT_RESOLVED"] |  |  |  |  |  |  |  |

## sensex

- URL: `http://140.245.226.102:10000/public/sensex.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.schema_version` | {"str": 3} | 3/3 | ["3.0"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["SENSEX"] |  |  |  |  |  |  |  |
| `$.security_id` | {"str": 3} | 3/3 | ["51"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["IDX_I"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["INDEX"] |  |  |  |  |  |  |  |
| `$.session` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.session.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.session.date` | {"str": 3} | 3/3 | ["2026-09-24"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.session.timezone` | {"str": 3} | 3/3 | ["Asia/Kolkata"] |  |  |  |  |  | name looks time-related |  |
| `$.session.current_time_ist` | {"str": 3} | 3/3 | ["2026-09-24 10:35:10 IST", "2026-09-24 10:35:31 IST", "2026-09-24 10:35:52 IST"] |  |  |  |  |  | name looks time-related | 2 |
| `$.feed` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.feed.status` | {"str": 3} | 3/3 | ["CONNECTED"] |  |  |  |  |  |  |  |
| `$.feed.messages` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.feed.quote_packets` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.feed.last_error` | {"str": 3} | 3/3 | [""] |  |  |  |  |  |  |  |
| `$.feed.last_tick_received_epoch` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ltp` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ltp_timestamp` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.timeframes` | {"list": 3} | 3/3 | [] |  |  |  |  | [4, 4] | name looks time-related |  |
| `$.timeframes[]` | {"str": 12} | 12/12 | ["1m", "5m", "15m"] |  |  |  |  |  | name looks time-related |  |
| `$.candle_source` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.candle_source.1m` | {"str": 3} | 3/3 | ["DHAN_WEBSOCKET_FULL"] |  |  |  |  |  |  |  |
| `$.candle_source.5m` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.candle_source.15m` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.candle_source.1h` | {"str": 3} | 3/3 | ["DHAN_HISTORICAL_API"] |  |  |  |  |  |  |  |
| `$.synthetic_candles` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.1m` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.1m[]` | {"dict": 9} | 9/9 | [] |  |  |  |  |  |  |  |
| `$.1m[].timestamp` | {"str": 9} | 9/9 | ["2026-09-24 09:15:00 IST", "2026-09-24 09:16:00 IST", "2026-09-24 09:17:00 IST"] |  |  |  |  |  | name looks time-related |  |
| `$.1m[].open` | {"float": 9} | 9/9 | [74272.4, 74317.65, 74216.93] | 74216.93 | 74317.65 |  |  |  |  |  |
| `$.1m[].high` | {"float": 9} | 9/9 | [74362.29, 74317.65, 74245.78] | 74245.78 | 74362.29 |  |  |  |  |  |
| `$.1m[].low` | {"float": 9} | 9/9 | [74120.62, 74210.93, 74208.49] | 74120.62 | 74210.93 |  |  |  |  |  |
| `$.1m[].close` | {"float": 9} | 9/9 | [74329.73, 74215.05, 74212.12] | 74212.12 | 74329.73 |  |  |  |  |  |
| `$.1m[].volume` | {"int": 9} | 9/9 | [204411, 115261, 106809] | 106809 | 204411 |  |  |  |  |  |
| `$.5m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.5m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.15m` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.15m[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.1h` | {"list": 3} | 3/3 | [] |  |  |  |  | [0, 0] |  |  |
| `$.1h[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |

## sensex-options

- URL: `http://140.245.226.102:10000/public/sensex-options.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["SENSEX"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["LIVE"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_OPTION_CHAIN_API"] |  |  |  |  |  |  |  |
| `$.security_id` | {"str": 3} | 3/3 | ["51"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["IDX_I"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["INDEX"] |  |  |  |  |  |  |  |
| `$.underlying_ltp` | {"float": 3} | 3/3 | [74141.44, 74139.07] | 74139.07 | 74141.44 |  |  |  |  | 1 |
| `$.expiry` | {"str": 3} | 3/3 | ["2026-09-24"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.expiry_list` | {"list": 3} | 3/3 | [] |  |  |  |  | [19, 19] |  |  |
| `$.expiry_list[]` | {"str": 57} | 57/57 | ["2026-09-24", "2026-10-01", "2026-10-08"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [196, 196] |  |  |
| `$.strikes[]` | {"dict": 588} | 588/588 | [] |  |  |  |  |  |  |  |
| `$.strikes[].strike` | {"float": 588} | 588/588 | [67000.0, 67100.0, 67200.0] | 67000.0 | 91000.0 |  |  |  |  |  |
| `$.strikes[].ce` | {"dict": 588} | 588/588 | [] |  |  |  |  |  |  |  |
| `$.strikes[].ce.average_price` | {"int": 252, "float": 336} | 588/588 | [0, 4278, 3492.69] | 0 | 4278 | 249 |  |  |  | 24 |
| `$.strikes[].ce.greeks` | {"dict": 588} | 588/588 | [] |  |  |  |  |  |  |  |
| `$.strikes[].ce.greeks.delta` | {"int": 300, "float": 288} | 588/588 | [0, 0.9349, 0.77368] | 0 | 0.97946 | 300 |  |  |  | 62 |
| `$.strikes[].ce.greeks.theta` | {"int": 300, "float": 288} | 588/588 | [0, -324.87488, -1537.9136] | -5845.0664 | 0 | 300 |  |  |  | 70 |
| `$.strikes[].ce.greeks.gamma` | {"int": 369, "float": 219} | 588/588 | [0, 5e-05, 7e-05] | 0 | 0.00094 | 369 |  |  |  | 15 |
| `$.strikes[].ce.greeks.vega` | {"int": 300, "float": 288} | 588/588 | [0, 3.47635, 7.75517] | 0 | 10.21947 | 300 |  |  |  | 69 |
| `$.strikes[].ce.implied_volatility` | {"int": 300, "float": 288} | 588/588 | [0, 87.53584283552568, 173.2535308824617] | 0 | 518.981468122176 | 300 |  |  |  | 70 |
| `$.strikes[].ce.last_price` | {"float": 506, "int": 82} | 588/588 | [9994.15, 0, 11176.5] | 0 | 11176.5 | 54 |  |  |  | 47 |
| `$.strikes[].ce.oi` | {"int": 588} | 588/588 | [1040, 0, 260] | 0 | 6589700 | 195 |  |  |  |  |
| `$.strikes[].ce.previous_close_price` | {"float": 504, "int": 84} | 588/588 | [9994.15, 0, 11176.5] | 0 | 11176.5 | 54 |  |  |  |  |
| `$.strikes[].ce.previous_oi` | {"int": 588} | 588/588 | [0, 3060, 280] | 0 | 2213920 | 210 |  |  |  |  |
| `$.strikes[].ce.previous_volume` | {"int": 588} | 588/588 | [0, 6780, 360] | 0 | 137716520 | 207 |  |  |  |  |
| `$.strikes[].ce.security_id` | {"int": 588} | 588/588 | [1121017, 1132785, 1133518] | 838729 | 1134766 |  |  |  |  |  |
| `$.strikes[].ce.top_ask_price` | {"float": 472, "int": 116} | 588/588 | [7654.3, 0, 6540.75] | 0 | 7654.3 | 98 |  |  |  | 88 |
| `$.strikes[].ce.top_ask_quantity` | {"int": 588} | 588/588 | [320, 0, 500] | 0 | 78100 | 98 |  |  |  | 82 |
| `$.strikes[].ce.top_bid_price` | {"float": 474, "int": 114} | 588/588 | [6507.3, 0, 5672.6] | 0 | 6531.45 | 96 |  |  |  | 88 |
| `$.strikes[].ce.top_bid_quantity` | {"int": 588} | 588/588 | [320, 0, 500] | 0 | 97020 | 96 |  |  |  | 76 |
| `$.strikes[].ce.volume` | {"int": 588} | 588/588 | [0, 60, 2040] | 0 | 52854900 | 249 |  |  |  | 58 |
| `$.strikes[].pe` | {"dict": 588} | 588/588 | [] |  |  |  |  |  |  |  |
| `$.strikes[].pe.average_price` | {"float": 271, "int": 317} | 588/588 | [0.46, 0, 0.48] | 0 | 10829.29 | 309 |  |  |  | 23 |
| `$.strikes[].pe.greeks` | {"dict": 588} | 588/588 | [] |  |  |  |  |  |  |  |
| `$.strikes[].pe.greeks.delta` | {"int": 385, "float": 203} | 588/588 | [0, -0.00085, -0.00122] | -0.99692 | 0 | 385 |  |  |  | 43 |
| `$.strikes[].pe.greeks.theta` | {"int": 385, "float": 203} | 588/588 | [0, -5.6004, -7.93401] | -450.5152 | 11.2597 | 385 |  |  |  | 58 |
| `$.strikes[].pe.greeks.gamma` | {"int": 434, "float": 154} | 588/588 | [0, 1e-05, 2e-05] | 0 | 0.00098 | 434 |  |  |  | 17 |
| `$.strikes[].pe.greeks.vega` | {"int": 385, "float": 203} | 588/588 | [0, 0.07483, 0.10436] | 0 | 10.21468 | 385 |  |  |  | 58 |
| `$.strikes[].pe.implied_volatility` | {"int": 331, "float": 257} | 588/588 | [0, 9.17085308188595, 9.050025522764956] | 0 | 86.6012460683124 | 331 |  |  |  | 58 |
| `$.strikes[].pe.last_price` | {"float": 460, "int": 128} | 588/588 | [0.35, 0, 0.3] | 0 | 58290.47 | 54 |  |  |  | 39 |
| `$.strikes[].pe.oi` | {"int": 588} | 588/588 | [59960, 0, 77600] | 0 | 4944760 | 249 |  |  |  |  |
| `$.strikes[].pe.previous_close_price` | {"float": 474, "int": 114} | 588/588 | [0.5, 0, 0.6] | 0 | 58290.47 | 54 |  |  |  |  |
| `$.strikes[].pe.previous_oi` | {"int": 588} | 588/588 | [73520, 0, 100860] | 0 | 2534820 | 249 |  |  |  |  |
| `$.strikes[].pe.previous_volume` | {"int": 588} | 588/588 | [518620, 0, 542880] | 0 | 101970640 | 246 |  |  |  |  |
| `$.strikes[].pe.security_id` | {"int": 588} | 588/588 | [1117487, 1133298, 1132683] | 837931 | 1134546 |  |  |  |  |  |
| `$.strikes[].pe.top_ask_price` | {"float": 470, "int": 118} | 588/588 | [0.35, 0, 0.4] | 0 | 17919.8 | 96 |  |  |  | 91 |
| `$.strikes[].pe.top_ask_quantity` | {"int": 588} | 588/588 | [5580, 0, 4480] | 0 | 189140 | 96 |  |  |  | 78 |
| `$.strikes[].pe.top_bid_price` | {"float": 463, "int": 125} | 588/588 | [0.3, 0, 0.35] | 0 | 14879.45 | 96 |  |  |  | 86 |
| `$.strikes[].pe.top_bid_quantity` | {"int": 588} | 588/588 | [2360, 0, 11200] | 0 | 107800 | 96 |  |  |  | 79 |
| `$.strikes[].pe.volume` | {"int": 588} | 588/588 | [189000, 0, 200440] | 0 | 98913300 | 309 |  |  |  | 61 |
| `$.updated_at` | {"str": 3} | 3/3 | ["2026-09-24T10:34:55.060824+05:30", "2026-09-24T10:35:30.756635+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.fetch_count` | {"int": 3} | 3/3 | [17737, 17739] | 17737 | 17739 |  |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.refresh_seconds` | {"float": 3} | 3/3 | [3.2] | 3.2 | 3.2 |  |  |  |  |  |
| `$.analytics` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.analytics.pcr_oi` | {"float": 3} | 3/3 | [0.6788823626553746] | 0.6788823626553746 | 0.6788823626553746 |  |  |  |  |  |
| `$.analytics.pcr_volume` | {"float": 3} | 3/3 | [1.288860823987461, 1.2888320375986309] | 1.2888320375986309 | 1.288860823987461 |  |  |  |  |  |
| `$.analytics.atm_strike` | {"float": 3} | 3/3 | [74100.0] | 74100.0 | 74100.0 |  |  |  |  |  |
| `$.analytics.max_pain_strike` | {"float": 3} | 3/3 | [74200.0] | 74200.0 | 74200.0 |  |  |  |  |  |
| `$.analytics.resistance_strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.analytics.resistance_strikes[]` | {"float": 9} | 9/9 | [74500.0, 74300.0, 74200.0] | 74200.0 | 74500.0 |  |  |  |  |  |
| `$.analytics.support_strikes` | {"list": 3} | 3/3 | [] |  |  |  |  | [3, 3] |  |  |
| `$.analytics.support_strikes[]` | {"float": 9} | 9/9 | [74000.0, 73800.0, 73500.0] | 73500.0 | 74000.0 |  |  |  |  |  |
| `$.analytics.total_call_oi` | {"float": 3} | 3/3 | [81142600.0] | 81142600.0 | 81142600.0 |  |  |  |  |  |
| `$.analytics.total_put_oi` | {"float": 3} | 3/3 | [55086280.0] | 55086280.0 | 55086280.0 |  |  |  |  |  |
| `$.analytics.total_call_volume` | {"float": 3} | 3/3 | [540999980.0, 543202760.0] | 540999980.0 | 543202760.0 |  |  |  |  |  |
| `$.analytics.total_put_volume` | {"float": 3} | 3/3 | [697273680.0, 700097120.0] | 697273680.0 | 700097120.0 |  |  |  |  |  |
| `$.analytics.avg_call_iv` | {"float": 3} | 3/3 | [44.884098087381346, 44.75997650012478] | 44.75997650012478 | 44.884098087381346 |  |  |  |  |  |
| `$.analytics.avg_put_iv` | {"float": 3} | 3/3 | [13.010046015304647, 13.528065864770506] | 13.010046015304647 | 13.528065864770506 |  |  |  |  |  |
| `$.analytics.iv_skew` | {"float": 3} | 3/3 | [31.8740520720767, 31.231910635354275] | 31.231910635354275 | 31.8740520720767 |  |  |  |  |  |
| `$.analytics.contracts` | {"list": 3} | 3/3 | [] |  |  |  |  | [392, 392] |  |  |
| `$.analytics.contracts[]` | {"dict": 1176} | 1176/1176 | [] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].security_id` | {"int": 1176} | 1176/1176 | [1121017, 1117487, 1132785] | 837931 | 1134766 |  |  |  |  |  |
| `$.analytics.contracts[].strike` | {"float": 1176} | 1176/1176 | [67000.0, 67100.0, 67200.0] | 67000.0 | 91000.0 |  |  |  |  |  |
| `$.analytics.contracts[].option_type` | {"str": 1176} | 1176/1176 | ["CE", "PE"] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].moneyness` | {"str": 1176} | 1176/1176 | ["ITM", "OTM"] |  |  |  |  |  |  |  |
| `$.analytics.contracts[].oi` | {"float": 1176} | 1176/1176 | [1040.0, 59960.0, 0.0] | 0.0 | 6589700.0 | 444 |  |  |  |  |
| `$.analytics.contracts[].volume` | {"float": 1176} | 1176/1176 | [0.0, 189000.0, 200440.0] | 0.0 | 98913300.0 | 558 |  |  |  |  |
| `$.analytics.contracts[].last_price` | {"float": 1176} | 1176/1176 | [9994.15, 0.35, 0.0] | 0.0 | 58290.47 | 108 |  |  |  |  |
| `$.analytics.contracts[].implied_volatility` | {"float": 1176} | 1176/1176 | [0.0, 9.17085308188595, 9.050025522764956] | 0.0 | 518.981468122176 | 631 |  |  |  |  |
| `$.analytics.contracts[].oi_change_classification` | {"str": 1176} | 1176/1176 | ["LONG_UNWINDING", "SHORT_COVERING"] |  |  |  |  |  |  |  |
| `$.analytics.data_quality` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.analytics.data_quality.contracts_total` | {"int": 3} | 3/3 | [392] | 392 | 392 |  |  |  |  |  |
| `$.analytics.data_quality.contracts_missing_security_id` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.analytics.data_quality.duplicate_security_ids` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.analytics.data_quality.crossed_markets_detected` | {"int": 3} | 3/3 | [0, 1] | 0 | 1 | 1 |  |  |  |  |

## sensex-depth

- URL: `http://140.245.226.102:10000/public/sensex-depth.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["SENSEX"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["ERROR"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_FULL_MARKET_DEPTH_WEBSOCKET"] |  |  |  |  |  |  |  |
| `$.underlying_security_id` | {"str": 3} | 3/3 | ["51"] |  |  |  |  |  |  |  |
| `$.exchange_segment` | {"str": 3} | 3/3 | ["BSE_FNO"] |  |  |  |  |  |  |  |
| `$.instrument` | {"str": 3} | 3/3 | ["OPTIDX"] |  |  |  |  |  |  |  |
| `$.depth_levels` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.underlying_ltp` | {"float": 3} | 3/3 | [74139.63, 74141.44, 74139.07] | 74139.07 | 74141.44 |  |  |  |  | 2 |
| `$.expiry` | {"str": 3} | 3/3 | ["2026-09-24"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.contract_count` | {"int": 3} | 3/3 | [50] | 50 | 50 |  |  |  |  |  |
| `$.contracts` | {"list": 3} | 3/3 | [] |  |  |  |  | [50, 50] |  |  |
| `$.contracts[]` | {"dict": 150} | 150/150 | [] |  |  |  |  |  |  |  |
| `$.contracts[].security_id` | {"str": 150} | 150/150 | ["839382", "839212", "881866"] |  |  |  |  |  |  |  |
| `$.contracts[].strike` | {"float": 150} | 150/150 | [72900.0, 73000.0, 73100.0] | 72900.0 | 75300.0 |  |  |  |  |  |
| `$.contracts[].option_type` | {"str": 150} | 150/150 | ["CE", "PE"] |  |  |  |  |  |  |  |
| `$.contracts[].expiry` | {"str": 150} | 150/150 | ["2026-09-24"] |  |  |  |  |  | parses as ISO-8601 |  |
| `$.contracts[].bid` | {"list": 150} | 150/150 | [] |  |  |  |  | [0, 0] |  |  |
| `$.contracts[].bid[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.contracts[].ask` | {"list": 150} | 150/150 | [] |  |  |  |  | [0, 0] |  |  |
| `$.contracts[].ask[]` | {} | 0/0 | [] |  |  |  |  |  |  |  |
| `$.contracts[].last_price` | {"float": 142, "int": 8} | 150/150 | [1223.8, 3.2, 1167.25] | 3.2 | 1223.8 |  |  |  |  | 93 |
| `$.contracts[].average_price` | {"float": 149, "int": 1} | 150/150 | [1309.39, 3.3, 1198.24] | 3.3 | 1309.39 |  |  |  |  | 79 |
| `$.contracts[].buy_quantity` | {"int": 150} | 150/150 | [98380, 1023120, 674220] | 98380 | 8360920 |  |  |  |  | 100 |
| `$.contracts[].sell_quantity` | {"int": 150} | 150/150 | [5920, 77280, 10780] | 5920 | 1049340 |  |  |  |  | 99 |
| `$.contracts[].volume` | {"int": 150} | 150/150 | [2820, 4621440, 65020] | 2820 | 99254120 |  |  |  |  | 97 |
| `$.contracts[].oi` | {"int": 150} | 150/150 | [2000, 709120, 13380] | 2000 | 6589700 |  |  |  |  |  |
| `$.contracts[].ohlc` | {"dict": 150} | 150/150 | [] |  |  |  |  |  |  |  |
| `$.contracts[].ohlc.open` | {"float": 120, "int": 30} | 150/150 | [1354.1, 3.65, 1600] | 1.45 | 1600 |  |  |  |  |  |
| `$.contracts[].ohlc.close` | {"float": 147, "int": 3} | 150/150 | [1918.25, 5.25, 1844.4] | 5.25 | 1918.25 |  |  |  |  |  |
| `$.contracts[].ohlc.high` | {"float": 108, "int": 42} | 150/150 | [1382.85, 4.4, 1600] | 4.4 | 1600 |  |  |  |  |  |
| `$.contracts[].ohlc.low` | {"float": 129, "int": 21} | 150/150 | [1201.25, 2.6, 1094.7] | 1.45 | 1201.25 |  |  |  |  |  |
| `$.contracts[].quote_updated_at` | {"str": 150} | 150/150 | ["2026-09-24T10:35:02.238243+05:30", "2026-09-24T10:35:02.238184+05:30", "2026-09-24T10:35:02.238345+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 | 100 |
| `$.contracts[].crossed_book` | {"bool": 150} | 150/150 | [false] |  |  |  |  |  |  |  |
| `$.updated_at` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.connection_count` | {"int": 3} | 3/3 | [595] | 595 | 595 |  |  |  |  |  |
| `$.packet_count` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.quote_refresh_seconds` | {"float": 3} | 3/3 | [1.0] | 1.0 | 1.0 |  |  |  |  |  |
| `$.error` | {"str": 3} | 3/3 | ["WebSocketConnectionClosedException: Connection to remote host was lost."] |  |  |  |  |  |  |  |

## sensex-indicators

- URL: `http://140.245.226.102:10000/public/sensex-indicators.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID_MASTER_INDICATOR"] |  |  |  |  |  |  |  |
| `$.engine_version` | {"str": 3} | 3/3 | ["1.0.0"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["SENSEX"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["OK"] |  |  |  |  |  |  |  |
| `$.timeframe` | {"str": 3} | 3/3 | ["1m"] |  |  |  |  |  | name looks time-related |  |
| `$.sync_count` | {"int": 3} | 3/3 | [4] | 4 | 4 |  |  |  |  |  |
| `$.result` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.symbol` | {"str": 3} | 3/3 | ["SENSEX"] |  |  |  |  |  |  |  |
| `$.result.security_id` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.previous_close` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.today_open` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.timeframe` | {"str": 3} | 3/3 | ["1m"] |  |  |  |  |  | name looks time-related |  |
| `$.result.synthetic_candles` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.bar_count` | {"int": 3} | 3/3 | [3] | 3 | 3 |  |  |  |  |  |
| `$.result.as_of` | {"str": 3} | 3/3 | ["2026-09-24T09:17:00+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.result.freshness` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.freshness.status` | {"str": 3} | 3/3 | ["FRESH"] |  |  |  |  |  |  |  |
| `$.result.freshness.age_seconds` | {"float": 3} | 3/3 | [107.0] | 107.0 | 107.0 |  |  |  |  |  |
| `$.result.freshness.reason` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.last_price` | {"float": 3} | 3/3 | [74212.12] | 74212.12 | 74212.12 |  |  |  |  |  |
| `$.result.price_change_from_previous_close_pct` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.price_change_from_today_open_pct` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.latest_bar` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.latest_bar.timestamp` | {"str": 3} | 3/3 | ["2026-09-24T09:17:00+05:30"] |  |  |  |  |  | name looks time-related, parses as ISO-8601 |  |
| `$.result.latest_bar.open` | {"float": 3} | 3/3 | [74216.93] | 74216.93 | 74216.93 |  |  |  |  |  |
| `$.result.latest_bar.high` | {"float": 3} | 3/3 | [74245.78] | 74245.78 | 74245.78 |  |  |  |  |  |
| `$.result.latest_bar.low` | {"float": 3} | 3/3 | [74208.49] | 74208.49 | 74208.49 |  |  |  |  |  |
| `$.result.latest_bar.close` | {"float": 3} | 3/3 | [74212.12] | 74212.12 | 74212.12 |  |  |  |  |  |
| `$.result.latest_bar.volume` | {"float": 3} | 3/3 | [106809.0] | 106809.0 | 106809.0 |  |  |  |  |  |
| `$.result.indicators` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicators.sma_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.ema_9` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.ema_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.vwap` | {"float": 3} | 3/3 | [74252.45403037104] | 74252.45403037104 | 74252.45403037104 |  |  |  |  |  |
| `$.result.indicators.vwma_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_middle_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_upper_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_lower_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_width_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.bb_percent_b_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.true_range` | {"float": 3} | 3/3 | [37.2899999999936] | 37.2899999999936 | 37.2899999999936 |  |  |  |  |  |
| `$.result.indicators.atr_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.natr_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.rsi_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.macd_line` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.macd_signal` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.macd_histogram` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.stoch_raw_k` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.stoch_k` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.stoch_d` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.cci_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.roc_12` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.momentum_10` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.williams_r_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.adx_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.plus_di_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.minus_di_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.obv` | {"float": 3} | 3/3 | [-222070.0] | -222070.0 | -222070.0 |  |  |  |  |  |
| `$.result.indicators.cmf_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.mfi_14` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.rvol_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.donchian_upper_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.donchian_lower_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.donchian_middle_20` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.keltner_middle` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.keltner_upper` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.keltner_lower` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.supertrend` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicators.supertrend_direction` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.result.indicator_status` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.sma_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.sma_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.sma_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.sma_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.ema_9` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_9.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_9.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.ema_9.required_observations` | {"int": 3} | 3/3 | [9] | 9 | 9 |  |  |  |  |  |
| `$.result.indicator_status.ema_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.ema_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.ema_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.vwap` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwap.ready` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwap.valid_observations` | {"int": 3} | 3/3 | [3] | 3 | 3 |  |  |  |  |  |
| `$.result.indicator_status.vwap.required_observations` | {"int": 3} | 3/3 | [1] | 1 | 1 |  |  |  |  |  |
| `$.result.indicator_status.vwma_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwma_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.vwma_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.vwma_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_middle_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_middle_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_middle_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_middle_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_upper_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_upper_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_upper_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_upper_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_lower_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_lower_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_lower_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_lower_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_width_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_width_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_width_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_width_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.bb_percent_b_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.true_range` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.true_range.ready` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.result.indicator_status.true_range.valid_observations` | {"int": 3} | 3/3 | [3] | 3 | 3 |  |  |  |  |  |
| `$.result.indicator_status.true_range.required_observations` | {"int": 3} | 3/3 | [1] | 1 | 1 |  |  |  |  |  |
| `$.result.indicator_status.atr_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.atr_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.atr_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.atr_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.natr_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.natr_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.natr_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.natr_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.rsi_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rsi_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rsi_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.rsi_14.required_observations` | {"int": 3} | 3/3 | [15] | 15 | 15 |  |  |  |  |  |
| `$.result.indicator_status.macd_line` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_line.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_line.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.macd_line.required_observations` | {"int": 3} | 3/3 | [26] | 26 | 26 |  |  |  |  |  |
| `$.result.indicator_status.macd_signal` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_signal.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_signal.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.macd_signal.required_observations` | {"int": 3} | 3/3 | [34] | 34 | 34 |  |  |  |  |  |
| `$.result.indicator_status.macd_histogram` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_histogram.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.macd_histogram.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.macd_histogram.required_observations` | {"int": 3} | 3/3 | [34] | 34 | 34 |  |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.stoch_raw_k.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.stoch_k` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_k.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_k.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.stoch_k.required_observations` | {"int": 3} | 3/3 | [16] | 16 | 16 |  |  |  |  |  |
| `$.result.indicator_status.stoch_d` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_d.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.stoch_d.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.stoch_d.required_observations` | {"int": 3} | 3/3 | [18] | 18 | 18 |  |  |  |  |  |
| `$.result.indicator_status.cci_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cci_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cci_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.cci_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.roc_12` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.roc_12.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.roc_12.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.roc_12.required_observations` | {"int": 3} | 3/3 | [13] | 13 | 13 |  |  |  |  |  |
| `$.result.indicator_status.momentum_10` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.momentum_10.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.momentum_10.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.momentum_10.required_observations` | {"int": 3} | 3/3 | [11] | 11 | 11 |  |  |  |  |  |
| `$.result.indicator_status.williams_r_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.williams_r_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.williams_r_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.williams_r_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.adx_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.adx_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.adx_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.adx_14.required_observations` | {"int": 3} | 3/3 | [27] | 27 | 27 |  |  |  |  |  |
| `$.result.indicator_status.plus_di_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.plus_di_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.plus_di_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.plus_di_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.minus_di_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.minus_di_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.minus_di_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.minus_di_14.required_observations` | {"int": 3} | 3/3 | [14] | 14 | 14 |  |  |  |  |  |
| `$.result.indicator_status.obv` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.obv.ready` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.result.indicator_status.obv.valid_observations` | {"int": 3} | 3/3 | [3] | 3 | 3 |  |  |  |  |  |
| `$.result.indicator_status.obv.required_observations` | {"int": 3} | 3/3 | [1] | 1 | 1 |  |  |  |  |  |
| `$.result.indicator_status.cmf_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cmf_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.cmf_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.cmf_20.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.mfi_14` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.mfi_14.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.mfi_14.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.mfi_14.required_observations` | {"int": 3} | 3/3 | [15] | 15 | 15 |  |  |  |  |  |
| `$.result.indicator_status.rvol_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rvol_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.rvol_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.rvol_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.donchian_upper_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.donchian_lower_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.donchian_middle_20.required_observations` | {"int": 3} | 3/3 | [21] | 21 | 21 |  |  |  |  |  |
| `$.result.indicator_status.keltner_middle` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_middle.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_middle.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.keltner_middle.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.keltner_upper` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_upper.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_upper.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.keltner_upper.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.keltner_lower` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_lower.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.keltner_lower.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.keltner_lower.required_observations` | {"int": 3} | 3/3 | [20] | 20 | 20 |  |  |  |  |  |
| `$.result.indicator_status.supertrend` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.supertrend.required_observations` | {"int": 3} | 3/3 | [10] | 10 | 10 |  |  |  |  |  |
| `$.result.indicator_status.supertrend_direction` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend_direction.ready` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.result.indicator_status.supertrend_direction.valid_observations` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.result.indicator_status.supertrend_direction.required_observations` | {"int": 3} | 3/3 | [10] | 10 | 10 |  |  |  |  |  |

## sensex-futures

- URL: `http://140.245.226.102:10000/public/sensex-futures.json`
- Headers: `{"date": "Thu, 24 Sep 2026 05:05:51 GMT", "cache-control": "no-store, no-cache, must-revalidate, max-age=0", "expires": "0", "content-type": "application/json"}`

| path | types | present | examples | min | max | zeros | nulls | list len | timestamp? | changed |
|---|---|---|---|---|---|---|---|---|---|---|
| `$` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.service` | {"str": 3} | 3/3 | ["PSYGRID"] |  |  |  |  |  |  |  |
| `$.symbol` | {"str": 3} | 3/3 | ["SENSEX"] |  |  |  |  |  |  |  |
| `$.status` | {"str": 3} | 3/3 | ["ERROR"] |  |  |  |  |  |  |  |
| `$.market_status` | {"str": 3} | 3/3 | ["OPEN"] |  |  |  |  |  |  |  |
| `$.market_open` | {"bool": 3} | 3/3 | [true] |  |  |  |  |  |  |  |
| `$.data_source` | {"str": 3} | 3/3 | ["DHAN_MARKET_QUOTE_API"] |  |  |  |  |  |  |  |
| `$.security_id` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.exchange_segment` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.instrument` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.trading_symbol` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.expiry` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.lot_size` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.tick_size` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.last_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.ohlc` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.volume` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.oi` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.oi_change` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.average_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.buy_quantity` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.sell_quantity` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.top_bid_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.top_ask_price` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  |  |  |
| `$.raw_quote` | {"dict": 3} | 3/3 | [] |  |  |  |  |  |  |  |
| `$.updated_at` | {"null": 3} | 3/3 | [null] |  |  |  | 3 |  | name looks time-related |  |
| `$.fetch_count` | {"int": 3} | 3/3 | [0] | 0 | 0 | 3 |  |  |  |  |
| `$.synthetic_data` | {"bool": 3} | 3/3 | [false] |  |  |  |  |  |  |  |
| `$.storage` | {"str": 3} | 3/3 | ["RAM_ONLY"] |  |  |  |  |  |  |  |
| `$.refresh_seconds` | {"float": 3} | 3/3 | [2.0] | 2.0 | 2.0 |  |  |  |  |  |
| `$.error` | {"str": 3} | 3/3 | ["RuntimeError: DHAN_SENSEX_FUTURES_NOT_RESOLVED"] |  |  |  |  |  |  |  |

# PSYGRID OPTIONS ENGINE v1.0

An intraday **options signal engine** for NIFTY, BANKNIFTY and SENSEX. It is a market-context
engine: it first works out where price is relative to meaningful levels and what price is doing
there, then requires independent sources to confirm the same event before it names a trade.

Outputs per index: **BUY CALL**, **BUY PUT**, **WATCH**, **NO TRADE**, **DATA GATE BLOCKED**,
**WARMING UP** or **MARKET CLOSED**.

> **Read-only research tool.** It never places orders and contains no broker or order API.
> The Signal Quality score is a confluence score. It is **not** a probability and has not been
> statistically calibrated. Nothing here promises profit.

---

## 1. Start it from a blank PowerShell window (Windows)

```powershell
# one-time: get the code
cd C:\
git clone -b claude/psygrid-options-data-inspect-bwotjj https://github.com/zahidshaikmohammed-cmyk/psygrid-derivatives-signals.git psygrid
cd C:\psygrid

# one-time: install dependencies
python -m pip install -r requirements.txt

# run the live engine (Ctrl+C to stop)
python run_engine.py
```

If you already cloned it earlier:

```powershell
cd C:\psygrid
git pull
python run_engine.py
```

Useful variants:

```powershell
python run_engine.py --interval 15          # poll every 15 s (default 20)
python run_engine.py --once                 # one cycle, then exit
python run_engine.py --ascii                # if ✓ ₹ ═ show as garbage in an old console
python run_engine.py --no-color --no-clear  # plain scrolling output
python run_engine.py --config my.json       # override settings (see section 5)
python run_engine.py --replay samples\raw\20260924_103510   # replay saved snapshots
python -m pytest -q                         # run the test suite (no network needed)
```

The engine needs about **12 minutes of continuous data** before it trusts market structure (see
"Known limitations"). Start it at or before 09:15 IST for the best results. If you restart during
the day, it reloads that day's price observations from `logs/`.

---

## 2. Decision flow

```
RAW DATA → DATA INTEGRITY → UNDERLYING → MARKET STRUCTURE → KEY LEVELS → LIQUIDITY
→ FUTURES → OPTIONS → DEPTH → INDICATORS → SETUP → CROSS-CONFLUENCE
→ STRIKE SELECTION → RISK → SIGNAL (+ state / dedup)
```

The engine asks, in order: *Where is price? What is the nearest major level? Is price approaching
it, testing it, rejecting it or breaking it? Has the break been accepted? What do futures, option
positioning, depth and volume say? Where is the invalidation?* Only after that does it decide
between BUY CALL, BUY PUT and NO TRADE.

---

## 3. Project tree

```
psygrid/
  config.py              every tunable (thresholds, weights, windows); JSON-overridable
  models.py              normalized data models (the only shapes analytics see)
  data_client.py         read-only HTTP client for the 15 endpoints (parallel, never raises)
  schema_adapter.py      raw JSON → models, using only observed field names
  data_integrity.py      DATA INTEGRITY GATE: per-feed OK/DEGRADED/BLOCKED + trading authorization
  market_clock.py        IST session phases, no hard-coded dates
  underlying_engine.py   observation store, internal 1m aggregation, HTF aggregation, persistence
  structure_engine.py    swings, HH/HL/LH/LL, trend, momentum, consolidation, OR, VWAP distance
  level_engine.py        INTELLIGENT LEVEL ENGINE: discovery, clustering, strength, tiers, state machine
  liquidity_engine.py    liquidity pools (equal highs/lows) and sweep + reclaim detection
  futures_engine.py      basis, basis change, futures momentum → 5-way classification
  option_chain_engine.py strike map, contract validation, OI maps, intraday option flows
  depth_engine.py        multi-level book imbalance (confirmation only)
  indicator_engine.py    uses only indicators the feed marks ready
  setup_engine.py        14 setup families, context filters, "waiting for …" explanations
  scoring_engine.py      cross-confluence + Signal Quality Score 0–100
  strike_selector.py     dynamic contract selection (never ATM by default)
  risk_engine.py         entry zone, invalidation, targets, option estimates, R:R, hold window
  signal_state.py        virtual FLAT/ACTIVE/T1/T2/INVALIDATED/CLOSED + deduplication
  signal_engine.py       orchestrator (per-index pipeline, logging hooks)
  monitor.py             terminal UI (ANSI colours, level map)
  logger.py              JSONL research logs + raw snapshot bundles
run_engine.py            entry point
tools/inspect_endpoints.py   Phase-1 live schema inspector
docs/SCHEMA.md           the schema actually observed on the live endpoints
samples/                 raw live responses + generated schema report (evidence)
tests/                   124 tests; fixtures are trimmed REAL payloads; sim.py builds scenarios
config.example.json      example override file
requirements.txt         requests, pytest
```

---

## 4. Installation

Requires Python 3.10+ (tested on 3.11). `requirements.txt`:

```
requests>=2.31
pytest>=8.0
```

```powershell
python -m pip install -r requirements.txt
```

---

## 5. Configuration

Every threshold lives in `psygrid/config.py` (`DEFAULTS`). To change settings, create a JSON file
containing only the keys you want to change and pass it with `--config`:

```powershell
copy config.example.json my.json
notepad my.json
python run_engine.py --config my.json
```

Unknown keys are rejected, so typos can't slip through. Settings you'll most likely want:

| key | default | meaning |
|---|---|---|
| `poll_interval_seconds` | 20 | polling cadence |
| `scoring.signal_threshold` / `watch_threshold` | 75 / 62 | quality needed for BUY / WATCH |
| `scoring.min_independent_confirmations` | 2 | futures / options / depth / volume / indicators that must agree |
| `scoring.weights.*` | see file | component weights |
| `levels.weights.*`, `levels.tier1_min_strength` | see file | level-strength model |
| `levels.acceptance_closes` | 3 | 1m closes beyond a level for ACCEPTED |
| `setups.min_room_ranges` | 3.0 | minimum room to the next major opposing level |
| `setups.max_chase_ranges` | 2.5 | no chasing beyond this distance from the level |
| `integrity.max_age_seconds.*` | 20–30 s | staleness limits per feed |
| `integrity.accepted_feed_status.*` | LIVE / OK | payload statuses accepted (fail-closed) |
| `session.no_new_entries_after` / `close_signals_at` | 15:00 / 15:20 | late-session rules |
| `options.max_spread_pct`, `options.delta_band`, `options.min/max_premium` | 3%, 0.30–0.70, per index | contract filters |

**None of these thresholds were fitted to live or future data.** Calibrate them later from
`logs/` on out-of-sample days.

---

## 6. Tests

```powershell
python -m pytest -q
```

124 tests, all offline. The fixtures are trimmed copies of the **real** live responses, and the
scenario simulator (`tests/sim.py`) edits those real payloads, so every test runs against the
exact live schema. Coverage:

malformed JSON · endpoint unavailable · timeout · HTTP 503 with a live payload · stale timestamps ·
future timestamps · zero prices · missing option fields · depth error (quote-only fallback and
blocked) · invalid/unrecognized market status · synthetic data · inconsistent underlying ·
impossible jumps · duplicate timestamps · indicator FRESH flag contradicted by `as_of` · strike
selection (not blindly ATM) · CALL setups · PUT setups · liquidity sweeps both ways · breakout +
acceptance · breakout + retest · failed breakout / breakdown · reclaim · clustering · futures
confirmation (symmetric) · depth symmetry and walls · conflicting signals · insufficient
confirmation · targets / invalidation / time stop / session close · deduplication and cooldown ·
no-trade chop · market closed / weekend / late session · **mirror anti-bias test** (a reflected
market must give BUY PUT with the same score as BUY CALL) · logging · replay of the real samples ·
CLI with unreachable endpoints.

---

## 7. What each module does

* **data_client**: fetches all 15 endpoints in parallel with timeout and one retry. It keeps
  non-2xx responses with their JSON body, because the server sends meaningful 503 payloads. It
  records the HTTP `Date` header.
* **schema_adapter**: maps the observed JSON into models. The option chain's placeholder 0 becomes
  `None` for prices, IV and greeks. Missing or mistyped fields become `None`; nothing is guessed.
  Futures fields have only ever been observed as null, so they are parsed defensively.
* **data_integrity**: evaluates each feed on payload status, market status, timestamp freshness
  (against a clock corrected by the server's HTTP `Date`), synthetic flags, crossed books and
  zero quotes. It also cross-checks the underlying across sources and rejects impossible jumps.
  It picks the underlying source (spot ltp → option-chain `underlying_ltp` → depth) and computes
  a data-quality score. **Trading is BLOCKED** when the option chain is unusable, no fresh
  underlying exists, the market isn't open, or sources disagree. Missing futures, depth or
  indicators only lower quality.
* **underlying_engine**: stores every verified price observation and persists it per day. It
  builds 1m bars (feed candles where they exist, otherwise `INTERNAL_AGG_1m` from observations) and
  aggregates 5m/15m bars only when at least 80% of the constituent minutes exist.
* **structure_engine**: works only inside contiguous bar segments, so a data gap is never read as
  price action. Computes fractal swings, HH/HL/LH/LL, trend, momentum in average-range units,
  expansion, consolidation, session high/low (flagged if observed only partially), opening range
  (only when fully observed) and VWAP (from the indicator feed, or from complete feed bars with
  volume).
* **level_engine** (primary decision layer): discovers candidates from previous-day levels (when
  the feed provides them), session extremes, opening range, 1m/5m/15m swings, VWAP, CE/PE OI
  concentration, OI change, server OI levels, max pain, futures levels, round numbers, liquidity
  pools and supply/demand bases. It clusters them into zones with stable IDs (`NIFTY_L_003`),
  scores strength 0–100 with configurable weights and a confluence bonus across independent
  families, and assigns Tier 1/2/3. It runs the state machine
  `UNTESTED → APPROACHING → TESTING → REJECTED | BROKEN → ACCEPTED | FAILED_BREAKOUT/BREAKDOWN →
  (retest) → RECLAIMED`, plus `INVALIDATED`, and reports price-to-level relationships.
* **liquidity_engine**: finds equal-high/low pools. A sweep counts only when the reference level
  existed before the sweep bar, the sweep bar made a new local extreme, price closed back within
  N bars, and the reclaim still holds.
* **futures_engine**: tracks basis, basis change and futures momentum, and classifies
  STRONG_BULLISH … STRONG_BEARISH_CONFIRMATION. It is never a trigger.
* **option_chain_engine**: builds the ±6-strike map and rejects contracts with no quote, a crossed
  quote, a wide spread, or no volume or OI. Derives intraday OI, volume and premium flows from its
  own poll history, activity expansion, and call-resistance / put-support maps.
* **depth_engine**: computes top-5 and full-book imbalance near ATM. Bullish means CE bid-heavy
  plus PE ask-heavy. A wall is only ever a note. In quote-only mode the score is halved.
* **indicator_engine**: uses VWAP, EMA9/20, MACD histogram, RSI regime and DI/ADX, but only when
  the feed marks them ready. It is not an RSI trigger.
* **setup_engine**: maps level events to SUPPORT BOUNCE, RESISTANCE REJECTION, LIQUIDITY SWEEP +
  RECLAIM, BREAKOUT/BREAKDOWN + ACCEPTANCE, BREAKOUT/BREAKDOWN + RETEST, FAILED
  BREAKOUT/BREAKDOWN, RANGE EXTREME REVERSAL, VWAP RECLAIM, VWAP REJECTION, MULTI-FACTOR LEVEL
  REACTION and MOMENTUM CONTINUATION. Every detector is written once with a direction sign, so
  CALL and PUT logic are symmetric. Context filters: no buying directly into an unbroken Tier-1
  opposing level, waiting for acceptance while a break is pending, and no chasing. Each filter
  tells you what the engine is **waiting for**.
* **scoring_engine**: 11 components on −1..+1 relative to the direction. Unavailable data counts
  as 0 but keeps its weight, and opposing evidence is penalized. A signal requires at least 2
  independent confirmations and at most 1 strong conflict.
* **strike_selector**: scores CE/PE contracts within ±4 strikes on delta closeness to 0.50,
  spread, liquidity, top-of-book size and IV versus neighbours, within premium and delta bands.
  Reports the reasons and the alternatives.
* **risk_engine**: sets the entry zone around LTP. Targets are the next Tier-1/2 levels, or
  1.5R/2.5R when none exist (labelled). Enforces minimum R:R and room to the next level. Option
  targets and invalidation are estimates from delta and gamma. Sets the holding window by setup
  family.
* **signal_state**: tracks virtual state and deduplicates signals (no repeats while one is
  active, cooldown after close or invalidation). After T1 the virtual stop moves to entry.
* **monitor / logger / run_engine**: terminal UI, JSONL logs and the CLI.

---

## 8. Endpoint schema actually discovered

See **[docs/SCHEMA.md](docs/SCHEMA.md)** for the full description, and
`samples/schema/20260924_103510/schema_report.md` for the machine-generated report.

### Feed status at capture time (2026-09-24 10:35 IST, from your machine)

| feed | NIFTY | BANKNIFTY | SENSEX |
|---|---|---|---|
| option chain | **usable** (LIVE, fresh) | **usable** | **usable** |
| underlying price | **usable** via option-chain `underlying_ltp` | same | same |
| depth | **usable** (20 levels) | **usable** | **degraded**: HTTP 503, websocket closed, empty ladders; fresh quote-level buy/sell totals used at half weight |
| futures | **blocked**: HTTP 503, `DHAN_NIFTY_FUTURES_NOT_RESOLVED` | **blocked** (same) | **blocked** (same) |
| indicators | **blocked**: HTTP 503, `STARTING` | **blocked**: `as_of` 09:16 but FRESH flag (stale) | **blocked**: `as_of` 09:17 (stale) |
| spot index | **blocked** as a live source: `ltp=null`, `feed.messages=0`, no candles | **blocked**: candles stop at 09:16 | **blocked**: candles stop at 09:17 |

Consequences with the feeds in this state: **futures confirmation is unavailable** (it costs up
to 10/106 of the score), **previous-day levels and VWAP are unavailable**, and underlying bars are
built internally from option-chain `underlying_ltp` samples. Signals are still possible when
option flows, depth, activity and structure agree, but the bar is higher. The engine re-evaluates
every feed every cycle, so when the server fixes futures, indicators or spot, they are picked up
automatically.

---

## 9. Known limitations

1. **No live verification from the build environment.** The cloud container that built this
   engine cannot reach `140.245.226.102` (its network policy blocks the host). The engine was
   verified against your real captured samples (replay) and against real-schema simulated
   markets. Run it on your machine for live behaviour.
2. **Futures fields have never been observed populated.** They are parsed by name and fail
   closed on unexpected types or statuses. Check the first live futures payload once the server
   resolves it.
3. **Warm-up.** Structure needs 12 contiguous 1m bars. Because spot candles and ltp are not live,
   bars are internally aggregated from option-chain `underlying_ltp` (sampled every poll). Their
   high/low only reflect sampled prices and they carry no volume.
4. **Previous-day levels and a complete opening range** exist only if the feed provides
   historical candles or the engine runs from 09:15. Otherwise they are marked unavailable.
5. **No aggressor side in the data.** Option-flow "participation" is evidence (OI build, volume
   dominance, premium change), not proof of buying or selling.
6. **Option targets are estimates** (delta + gamma; theta and IV change ignored).
7. **Scores are uncalibrated.** Thresholds are conservative defaults. Use the logs to calibrate
   on out-of-sample data before trusting any number.
8. Exchange holidays aren't hard-coded. The engine relies on weekday rules plus the feeds'
   `market_status`/`market_open`.
9. Active virtual signals aren't advanced while the data gate is blocked.

---

## 10. Example terminal output

### (a) Real data: replay of your captured samples

`python run_engine.py --replay samples\raw\20260924_103510 --no-color`, third round, verbatim:

```
════════════════════════════════════════════════════════════════
PSYGRID OPTIONS ENGINE v1.0   (signals only — no orders)
24-09-2026 10:35:52 IST   session: OPEN
════════════════════════════════════════════════════════════════
NIFTY   23,221.05   [OPTION_CHAIN.underlying_ltp]
  feeds spot:BLOCKED  options:OK  depth:OK  futures:BLOCKED  indicators:BLOCKED   data quality 0.50
    spot blocked: not a live price source: ltp=null, feed.status=CONNECTED, feed.messages=0; no 1m candles
    futures blocked: HTTP 503 (evaluated on JSON payload); status=ERROR (RuntimeError: DHAN_NIFTY_FUTURES_NOT_RESOLVED)
    indicators blocked: HTTP 503 (evaluated on JSON payload); status=STARTING
  RESISTANCE
     23,400  ─────────   35/100  T2  23,398–23,402   RESISTANCE
     23,300  ─────────   35/100  T2  23,298–23,302   RESISTANCE
  23,221.05  ●  PRICE
  SUPPORT
     23,200  ─────────   35/100  T2  23,198–23,202   SUPPORT  ← APPROACHING
     23,000  ─────────   31/100  T2  22,998–23,002   SUPPORT
  STATE: APPROACHING SUPPORT 23,200 (NIFTY_L_005)
  unavailable: previous-day high/low/close (not provided by feeds); opening range (incomplete observation of first minutes); VWAP (indicator feed not fresh and no volume bars)
DATA NOT READY — WARMING UP: warming up: 1/12 contiguous completed 1m bars
  bars: 2 (0 feed, 2 internally aggregated), first 10:34
────────────────────────────────────────────────────────────────
BANKNIFTY   55,568.35   [OPTION_CHAIN.underlying_ltp]
  feeds spot:BLOCKED  options:OK  depth:OK  futures:BLOCKED  indicators:BLOCKED   data quality 0.50
    spot blocked: not a live price source: ltp=null, feed.status=CONNECTED, feed.messages=0; last 1m candle closed 09:17 (79 min ago)
    futures blocked: HTTP 503 (evaluated on JSON payload); status=ERROR (RuntimeError: DHAN_BANKNIFTY_FUTURES_NOT_RESOLVED)
    indicators blocked: stale: latest bar (as_of+1m) 09:17:00 is 79 min old (max 180s); server freshness field says FRESH; overridden by as_of age
  ...
SENSEX   74,139.07   [OPTION_CHAIN.underlying_ltp]
  feeds spot:BLOCKED  options:OK  depth:DEGRADED  futures:BLOCKED  indicators:BLOCKED   data quality 0.38
    depth degraded: HTTP 503 (evaluated on JSON payload); status=ERROR (WebSocketConnectionClosedException: Connection to remote host was lost.); bid/ask ladders empty; using quote-level buy/sell totals (median quote age 2s)
  ...
SUMMARY
  NIFTY     : WARMING UP — warming up: 1/12 contiguous completed 1m bars
  BANKNIFTY : WARMING UP — warming up: 1/12 contiguous completed 1m bars
  SENSEX    : WARMING UP — warming up: 1/12 contiguous completed 1m bars
════════════════════════════════════════════════════════════════
```

### (b) A BUY CALL, from the test scenario

**Synthetic prices on the real schema, not live data.** Output from `tests/sim.py`,
`bull_breakout_path`:

```
NIFTY   23,227.20   [OPTION_CHAIN.underlying_ltp]
  feeds spot:BLOCKED  options:OK  depth:OK  futures:OK  indicators:OK   data quality 0.90
>>> BUY CALL <<<
Strike       : 23,200 CE
Option LTP   : ₹86.20  (bid 86.15 / ask 86.25, spread 0.12%)
Underlying   : 23,227.20
SETUP        : BREAKOUT + ACCEPTANCE
KEY LEVEL    : 23,194 (NIFTY_L_008)
LEVEL TYPE   : MAJOR RESISTANCE → SUPPORT
LEVEL STRENGTH: 100/100
MARKET STATE : ACCEPTANCE ABOVE LEVEL
Entry        : ₹84.50–87.90
Invalidation : NIFTY 23,175.25  (option est. ₹60.00)
Target 1     : NIFTY 23,305.13  (option est. ₹139.25)
Target 2     : NIFTY 23,357.08  (option est. ₹183.80)
R:R (T1)     : 1.50   targets from R-multiples (no opposing key level mapped)
EXPECTED HOLD: SHORT INTRADAY MOMENTUM (5-30 min)
QUALITY      : 77/100  (confluence score, not a probability)
Time         : 24-09-2026 10:22:20 IST
CONFIRMATION
[✓] Underlying structure             trend RANGE, EH/EL, last 3 bars +1.00
[✓] Key level                        MAJOR RESISTANCE → SUPPORT 23,194 strength 100
[✓] Futures confirmation             BULLISH_CONFIRMATION
[✓] Momentum                         +2.99 ranges (UP)
[✓] Volume / participation expansion options activity x1.27
[✓] Option participation             volume_flow +0.43, oi_flow +1.00, premium_flow +1.00
[✓] Depth confirmation               FULL: CE +0.33 / PE -0.33
[✓] VWAP / indicators                price above VWAP 23179.5, EMA9 > EMA20
[✓] Contract liquidity               23,200CE spread 0.12%
```

Before this signal the same run showed `BREAKOUT at 23,196 — WAIT FOR ACCEPTANCE (n closes so
far)` for three minutes. The mirrored market produced **BUY PUT 23,200 PE, BREAKDOWN +
ACCEPTANCE, Q77** at the same second.

### (c) NO TRADE and DATA GATE BLOCKED, from the test scenarios

A choppy market with the real futures/indicator error payloads (`tests/sim.py`, `chop_path`):

```
NIFTY   23,207.69   [OPTION_CHAIN.underlying_ltp]
  feeds spot:BLOCKED  options:OK  depth:OK  futures:BLOCKED  indicators:BLOCKED   data quality 0.50
  RESISTANCE
     23,218  ═════════   69/100  T1  23,216–23,219   MAJOR RESISTANCE  ← TESTING
  AT PRICE
     23,199  ═════════  100/100  T1  23,192–23,213   MAJOR DEMAND  ← TESTING
  23,207.69  ●  PRICE
  SUPPORT
     23,000  ─────────   35/100  T2  22,998–23,002   SUPPORT
  trend RANGE, momentum -1.1
  STATE: AT SUPPORT 23,199 (NIFTY_L_007)
  STATE: AT RESISTANCE 23,218 (NIFTY_L_015)
NO TRADE
  reason: no valid setup at a meaningful level
  waiting for: 23,218 reaction seen — waiting for a confirming close
  waiting for: TESTING MAJOR DEMAND 23,199 — waiting for acceptance beyond or rejection
  waiting for: TESTING MAJOR RESISTANCE 23,218 — waiting for acceptance beyond or rejection
```

The option chain arriving 46 s late:

```
NIFTY   n/a
  feeds spot:BLOCKED  options:BLOCKED  depth:BLOCKED  futures:BLOCKED  indicators:BLOCKED   data quality 0.00
    options blocked: stale: updated_at 09:59:59 is 46s old (max 30s)
    depth blocked: stale: updated_at 09:59:59 is 46s old (max 20s)
    futures blocked: stale: updated_at 09:59:59 is 46s old (max 20s)
    indicators blocked: HTTP 503 (evaluated on JSON payload); status=STARTING
DATA GATE BLOCKED — TRADING AUTHORIZATION = BLOCKED
  reason: option chain unusable: stale: updated_at 09:59:59 is 46s old (max 30s)
  reason: no fresh underlying price from any source
```

## 11. Logs (for later calibration)

`logs/<YYYY-MM-DD>/`: `decisions.jsonl` (every index, every cycle, with all score components),
`signals.jsonl`, `events.jsonl` (T1/T2/invalidated/closed), `data_quality.jsonl`,
`<INDEX>_observations.jsonl` and `raw/*.json.gz` (raw bodies and HTTP metadata per cycle).
Raw bundles run to roughly 100–200 MB per day at a 20 s poll. Set `logging.raw_snapshots` to
`false` to disable them.

---

## 12. Audit summary

A full audit was done after the first working build. Defects found and fixed:

| # | area | defect | fix |
|---|---|---|---|
| 1 | structure | 09:15–09:17 feed bars and 10:34 internal bars were treated as adjacent (77-min gap read as price action) | contiguous-segment analysis for swings, momentum, sweeps and VWAP setups |
| 2 | setups | a stale support-bounce event fired a CALL 50 pts away from its level while resistance had only just broken | chase limit on every level event, plus "wait for acceptance" while a break is pending |
| 3 | levels | first-element clustering split zones and reset their state/history | single-linkage clustering with a max width, plus overlap-based zone matching |
| 4 | liquidity | a zone created after a bar could serve as that bar's swept level (look-ahead) | zone formation = first time the engine saw it; the sweep bar must be a new local extreme |
| 5 | levels | after a bar-close breakout failure, the next tick was misread as a gap through the zone (FAILED_BREAKOUT overwritten by a bogus BROKEN DOWN) | crossing requires two consecutive observations on opposite sides; side reset on failure |
| 6 | levels | a retest after APPROACHING lost the "retest of accepted break" flag | carry the pre-approach state into TESTING |
| 7 | levels | a successful break after an earlier failed break wasn't labelled RECLAIMED | reclaim detection includes prior failures |
| 8 | risk | gamma term had the wrong sign for adverse moves | convexity term +½γΔ² |
| 9 | signal state | emitted signal's invalidation mutated after T1 | separate virtual `stop` field; emitted record immutable |
| 10 | integrity | stale indicator bar close could block trading via the cross-check | indicator divergence only disqualifies the indicator feed |
| 11 | structure | fractal swings missed flat tops (strict ties) | left-strict / right-inclusive fractals |
| 12 | underlying | an in-progress feed candle would have been treated as complete | completeness derived from bar end time |
| 13 | logging | about 5,400 raw files per hour | one gzip bundle per cycle |
| 14 | integrity | server FRESH flag contradicted by `as_of` | freshness computed locally from `as_of`; the contradiction is reported |

Checks after fixes: `pytest` 124/124 pass, `pyflakes` clean, and the mirror test shows identical
BUY CALL / BUY PUT scores.

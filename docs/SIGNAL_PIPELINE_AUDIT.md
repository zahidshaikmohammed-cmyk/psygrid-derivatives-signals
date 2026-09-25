# Signal-capability audit: can a genuine setup actually reach BUY CALL / BUY PUT?

Forensic audit of the full decision pipeline, run against the code as of this
document's commit. Goal: **"selective but capable"**, not "no signals" and not
"signal everything". Every claim below is either (a) read directly from the
source at the cited file:line, or (b) demonstrated by a named, currently-passing
test that exercises the real production decision path (`PsygridEngine.cycle()`
via `IndexPipeline.run()`), never a shortcut around it. No threshold, weight,
confirmation count, or data-integrity rule was changed to produce these results.

## Executive summary

**The engine is not signal-starved as a blanket matter.** `tests/test_scenarios.py`
already proved, before this audit, that a genuine simulated breakout reaches
`BUY CALL` (`test_breakout_acceptance_emits_single_buy_call`) and its exact
mirror reaches `BUY PUT` (`test_mirror_scenario_emits_buy_put_with_same_quality`)
through the unmodified production path. This audit did not find a bug that makes
either direction structurally unreachable.

What the audit *did* find was an **observability gap**: a NO_TRADE or WATCH
result gave at most 1-3 truncated reason strings, with no way to see which of
the confirmation sources passed, which were missing, why they were missing, or
how many points short of the threshold the score actually was. That made it
genuinely hard to tell "no real setup exists" apart from "a real setup exists
and is one confirmation away". That gap is fixed by this audit (see
[Fixes made](#fixes-made)). No scoring, threshold, confirmation-count, or
data-integrity logic was touched.

## Pipeline map

```
RAW ENDPOINTS (data_client.py)
  -> DATA NORMALIZATION (schema_adapter.py: ADAPTERS[feed])
  -> DATA INTEGRITY (data_integrity.py: IntegrityGate.evaluate)
  -> UNDERLYING PRICE (data_integrity.py source selection: spot -> options -> depth)
  -> HISTORY / WARMUP (underlying_engine.py: UnderlyingTracker; structure_engine.py: min_bars)
  -> STRUCTURE (structure_engine.py: StructureEngine.analyze)
  -> LEVEL ENGINE (level_engine.py: LevelEngine.discover/cluster/score/update)
  -> LIQUIDITY (liquidity_engine.py: LiquidityEngine.analyze)
  -> SETUP DETECTION (setup_engine.py: SetupEngine.detect)
  -> OPTIONS (option_chain_engine.py: OptionChainEngine.analyze)
  -> DEPTH (depth_engine.py: DepthEngine.analyze)
  -> FUTURES (futures_engine.py: FuturesEngine.analyze)
  -> INDICATORS (indicator_engine.py: IndicatorEngine.analyze)
  -> CONFIRMATIONS + SCORING (scoring_engine.py: ScoringEngine.components/score)
  -> RISK (risk_engine.py: RiskEngine.plan)
  -> STRIKE SELECTION (strike_selector.py: StrikeSelector.select)
  -> SIGNAL AUTHORIZATION (signal_engine.py: IndexPipeline.run, the SIGNAL/WATCH/NO_TRADE grade)
  -> LIFECYCLE / DEDUP (signal_state.py: SignalStateManager.consider/track)
  -> Signal (signal_state.py dataclass; this repo's TradeReadySignal-equivalent)
  -> TELEGRAM (telegram_notifier.py, wired from run_engine.py::notify_new_signals)
```

| stage | input | output | hard blocker | soft deduction | on failure |
|---|---|---|---|---|---|
| Raw endpoints | HTTP GET, `data_client.py` | `RawResponse` per feed | none — every transport/HTTP failure is captured, never raised (`data_client.py:71-83`) | — | feed's own `FeedCheck` becomes BLOCKED downstream |
| Normalization | `RawResponse.payload` | typed model (`SpotData`/`OptionChain`/...) or `None` + issues | adapter exception -> `model=None` (`signal_engine.py:132-137`, never crashes the cycle) | — | feed BLOCKED |
| Data integrity | typed models | `GateResult` (AUTHORIZED / BLOCKED) | option chain unusable, no fresh underlying price, cross-source price divergence, synthetic data, stale timestamp (`data_integrity.py:305-324`) | missing futures/depth/indicators only lower `data_quality`, never block (`data_integrity.py:17-18`) | `DATA_GATE_BLOCKED` |
| Underlying price | spot/options/depth | `u_price` | none of the three sources fresh | source preference: spot > options > depth (`data_integrity.py:262-269`) | `no fresh underlying price` -> BLOCKED |
| Warmup | 1m bars | `StructureState.ready` | `< min_bars` (12) contiguous **completed** bars in the current gap-bounded segment (`structure_engine.py:167-171`) | a >3 min gap starts a fresh segment (`structure_engine.py:74-84`) | `WARMING_UP`, setup detection never runs (`setup_engine.py:87-89`) |
| Structure | bars, price | trend/momentum/VWAP/swings | none (always produces a state once `ready`) | — | feeds level/setup engines |
| Level engine | structure, chain, futures levels, swings | `LevelMap` of scored `Zone`s | none | fewer evidence families -> lower zone `strength`/tier (`level_engine.py:350-377`) | fewer/weaker levels for setups to react to |
| Liquidity | bars, zones | sweeps/pools | none | — | feeds setup detection (sweep+reclaim setups) |
| Setup detection | levels + liquidity + structure + VWAP | `SetupCandidate`s | not `st.ready`; zone event stale (>`max_event_age_seconds`); price not yet beyond the zone edge; extended too far to chase; a nearer unbroken opposing major level (`setup_engine.py:109-224`) | none (binary candidate/no-candidate) | candidate rejected with a specific reason in `res.rejected`/`res.waiting` |
| Options | chain, price | `ChainState` (participation, activity) | chain unusable/no price -> `available=False` | first 1-3 polls: participation/activity are `None` ("building history") | that confirmation source unavailable this cycle, never blocks the cycle |
| Depth | depth data, ATM/step | `DepthState` (score) | no depth contracts near ATM, or missing one option side | `QUOTE_ONLY` mode halves the score (`depth_engine.py:74-76`) | confirmation source unavailable |
| Futures | futures data | `FuturesState` (score) | feed unusable / no price | `NEUTRAL` (score 0) until move >= `confirm_ranges` (`futures_engine.py:66-71`) | confirmation source unavailable or neutral (never a strict blocker) |
| Indicators | indicator data | `IndicatorState` (score) | feed unusable / no price | `not ind.values` -> DEGRADED, not blocked (`data_integrity.py:256-258`) | confirmation source unavailable |
| Confirmations + scoring | all components above | `ScoreResult` (score, grade, confirmations, conflicts) | `len(conflicts) > 1` OR `len(confirmations) < 2` (`scoring_engine.py:131-136`) | missing component contributes 0 but keeps its weight in the denominator (`scoring_engine.py:9-10`) | `NO_TRADE`, reason = conflict list or confirmation count |
| Risk | candidate, selection, levels | `RiskPlan` or rejection | R:R below `min_reward_risk` given the nearest opposing level (`risk_engine.py:79-81`); invalidation on wrong side of price (`risk_engine.py:68-69`) | — | candidate has `plan=None`, excluded from `tradable` |
| Strike selection | chain, direction, price | `Selection` or `None` | premium out of band, delta out of band, empty top-of-book, crossed/no quote (`strike_selector.py:66-76`) | contract scored 0..1 on delta/spread/liquidity/book/IV, best picked | `no eligible contract`, candidate excluded from `tradable` |
| Signal authorization | scored+risked candidates | `dec.status` | `grade != SIGNAL` or `plan is None` for every candidate (`signal_engine.py:237`) | — | `WATCH` (grade WATCH) or `NO_TRADE` |
| Lifecycle/dedup | new `Signal` | accept/suppress | same direction already active; identical (direction, strike, type, setup, level) closed within cooldown and no `requalify_score_jump`; direction just invalidated within cooldown (`signal_state.py:144-165`) | — | `dec.signal=None`, status falls back to `SIGNAL_ACTIVE`/`NO_TRADE` |
| Telegram | `dec.signal` | Telegram message or nothing | notifier disabled, network/HTTP error, unexpected exception (`telegram_notifier.py`, `run_engine.py::notify_new_signals`) — all non-raising | — | logged to stderr, never affects `dec.status` or authorization |

## Signal-starvation point inventory (Phase 2)

Every condition below that can prevent `BUY CALL`/`BUY PUT`, with its classification:

| # | condition | file:line | classification |
|---|---|---|---|
| 1 | `market_open`/`session.status` not accepted | `data_integrity.py:120-122` | INTENTIONAL SAFETY GATE |
| 2 | option chain unusable (status, freshness, quote count) | `data_integrity.py:164-184` | INTENTIONAL SAFETY GATE (critical dependency, documented) |
| 3 | no fresh underlying price from any of 3 sources | `data_integrity.py:309-310` | INTENTIONAL SAFETY GATE |
| 4 | cross-source underlying divergence > 0.30% | `data_integrity.py:287-293` | INTENTIONAL SAFETY GATE |
| 5 | impossible tick jump > 2%/120s | `data_integrity.py:300-303` | INTENTIONAL SAFETY GATE |
| 6 | < 12 contiguous completed 1m bars | `structure_engine.py:167` | INTENTIONAL SAFETY GATE, see [Warmup audit](#warmup-audit) |
| 7 | no `SetupCandidate` at all this cycle | `setup_engine.py:224` (empty `res.candidates`) | NO ISSUE — correctly means "no event happened" |
| 8 | zone event older than `max_event_age_seconds` (360s) | `setup_engine.py:100-104` | INTENTIONAL SAFETY GATE |
| 9 | price extended beyond `max_chase_ranges` (2.5R) from the level | `setup_engine.py:113-117` | INTENTIONAL SAFETY GATE ("no chasing"), tested (`test_no_chasing_after_extended_breakout`) |
| 10 | a nearer unbroken major opposing level within `min_room_ranges` (3R) | `setup_engine.py:215-223` | INTENTIONAL SAFETY GATE |
| 11 | invalidation on the wrong side of price | `setup_engine.py:206-208` | INTENTIONAL SAFETY GATE (sanity check) |
| 12 | `len(conflicts) > max_strong_conflicts` (1) | `scoring_engine.py:131` | INTENTIONAL SAFETY GATE |
| 13 | `len(confirmations) < min_independent_confirmations` (2) | `scoring_engine.py:133` | INTENTIONAL SAFETY GATE — see [Independent confirmation audit](#independent-confirmation-audit) |
| 14 | `score < signal_threshold` (75) with confirmations/conflicts satisfied | `scoring_engine.py:137-141` | INTENTIONAL SAFETY GATE — see [Score audit](#score-distribution--threshold-audit) |
| 15 | R:R below `min_reward_risk` given nearest opposing level | `risk_engine.py:79-81` | INTENTIONAL SAFETY GATE |
| 16 | no eligible contract (premium/delta/spread/book/quote) | `strike_selector.py:66-76` | INTENTIONAL SAFETY GATE |
| 17 | same direction already active for the index | `signal_state.py:148-149` | INTENTIONAL SAFETY GATE (one live signal per index) |
| 18 | identical setup identity within cooldown after close | `signal_state.py:155-156` | INTENTIONAL SAFETY GATE (anti-whipsaw) |
| 19 | same direction within cooldown after an invalidation | `signal_state.py:157-158` | INTENTIONAL SAFETY GATE |
| 20 | new entries disabled after 15:00 IST | `market_clock.py:53-54`, `signal_engine.py:210-213` | INTENTIONAL SAFETY GATE, tested (`test_no_new_entries_late_session`) |

No condition in this table was found to be **unconditionally** unreachable
(every gate above is demonstrably passable — see the CALL/PUT positive-control
tests). None is classified REAL BUG.

## Independent confirmation audit (Phase 3)

`INDEPENDENT = ("futures", "options", "depth", "volume", "vwap_indicators")`
(`scoring_engine.py:29`). Note what is **excluded**: `structure`, `level`,
`momentum`, `setup` — the price-action components that *generated* the
candidate in the first place. This is deliberate: a setup cannot confirm
itself with the same evidence that produced it. That is a legitimate
architectural choice, not a bug, but it does mean **all** required
confirmation must come from data genuinely independent of price structure:// futures, options order flow, depth, volume, and VWAP/indicators.

The user's specific worry — "if VWAP confirmation + indicator confirmation
count as 2 independent confirmations, are they really independent?" — does
**not apply to this codebase**: `vwap_indicators` is a **single** component
(`scoring_engine.py:107-113`), built either from the combined indicator score
(VWAP + EMA + MACD + RSI + DI averaged into one value) or, only when
indicators are unavailable, from raw VWAP distance. VWAP and "indicators" can
never be double-counted as two separate confirmations from the same
underlying signal. **Verified, no issue.**

Availability under normal conditions, per source:

- **futures**: needs the feed usable and >= 2 polls of history (`futures_engine.py:44,56`). Scores 0.0 (NEUTRAL, does not count) unless futures' own move is >= `confirm_ranges` (0.5 avg ranges) — common outside a genuine directional move, and *correctly* so: futures shouldn't "confirm" a setup it isn't itself moving on.
- **options** (participation): needs >= 2 polls of flow history, ideally `participation_polls` (4) (`option_chain_engine.py:144-147`); reads real OI/volume/premium deltas between polls. **Cold-start property**: unavailable (`None`) for the first 1-3 cycles after any engine (re)start, regardless of price action strength.
- **depth**: needs contracts near ATM with two-sided books (or quote-level totals in `QUOTE_ONLY`). The scoring multiplies the raw imbalance by 2 before clipping (`scoring_engine.py:104`), so even a modest 0.25 imbalance saturates near the confirmation threshold — this component is, if anything, *easier* than its peers to trigger, not a starvation risk.
- **volume**: needs either options `activity_expansion` (>= 4 polls of increasing total volume, `option_chain_engine.py:178-184`) or indicator `rvol_20`. The **slowest-to-arm** of the five — a genuine breakout's volume expansion needs several polls (~1-2 min at a 20s interval) to register as "expansion" relative to its own recent baseline, by construction (there is no external volume baseline to compare against day one).
- **vwap_indicators**: the most reliably available — either a fresh indicator score or, failing that, raw VWAP distance computed straight from structure's own VWAP (available as soon as `st.vwap` exists).

**Conclusion**: under a real, sustained directional move, 2+ of these 5 do
become available and aligned — this is exactly what
`test_breakout_acceptance_emits_single_buy_call` and
`test_mirror_scenario_emits_buy_put_with_same_quality` demonstrate end to end.
The genuine risk is **cold start** (the first ~1-2 minutes after the engine
starts or restarts, before options/volume history exists) and **weak/early**
setups where price has just crossed a level but flow hasn't caught up yet —
both are legitimate, already-observable states (`"building option-flow
history"`, `"building baseline"`), not silent failures. This is a DATA
AVAILABILITY characteristic of the architecture, not a bug: it cannot be
fixed without inventing data that doesn't exist yet, which the instructions
for this audit explicitly rule out.

## Score distribution / threshold audit (Phase 8)

Weights (`config.py` `scoring.weights`): structure 14, level 16, futures 10,
momentum 10, volume 8, options 12, liquidity 8, depth 8, vwap_indicators 8,
setup 6, data_quality 6. **Total = 106.**

`score = 100 * (pos - 0.5*neg) / 106`, clipped to [0, 100].

- **Theoretical maximum** (every component at its clipped extreme of +1) = 100.
  Not achievable in practice: `level` (zone strength/100) and `setup`
  (`quality`, capped at 0.90 for the strongest setup family, `BASE_QUALITY`
  in `setup_engine.py:32-40`) cannot reach 1.0 by construction.
- **A realistic, solidly-confirmed but not exceptional setup** — decent zone
  strength (~0.75), strong momentum (1.0), one futures/vwap confirmation each
  at moderate strength, modest volume/options participation, a good (not
  perfect) contract — computes to roughly **68-72**: comfortably inside
  `WATCH` (>= 62) but short of `signal_threshold` (75). This is not a bug in
  the arithmetic; it means the configured threshold intentionally requires
  more than "solid" — it requires several components genuinely aligned near
  their strong end simultaneously.
- **Empirically, that bar is reachable**: the simulated clean breakout in
  `tests/test_scenarios.py` (`bull_breakout_path`, which injects a real,
  sustained, multi-source-confirmed move — futures momentum, options OI/
  volume flow, depth imbalance, and price all moving together) scores
  **77.4/100** at the moment of signal (verified live during this audit;
  see `test_breakout_acceptance_emits_single_buy_call`'s
  `s.score >= signal_threshold` assertion). The threshold is not
  mathematically or logically impossible to reach under normal directional
  conditions — it requires genuine, multi-source confluence, which is the
  documented intent ("Signal Quality score is a confluence score ... not a
  probability", `README.md`).

**No practical-maximum bug was found.** The score can and does reach the
threshold for a genuinely strong setup; it correctly stays below threshold
for a merely-plausible one. Recalibrating the exact number is explicitly out
of scope for this audit (and the codebase's own docstrings already say the
weights are uncalibrated placeholders pending real outcome logs).

## Warmup / history audit (Phase 9)

- `min_bars = 12` contiguous **completed** 1-minute bars, computed only over
  the tail segment after the last >3-minute gap (`structure_engine.py:74-89,
  167`). This is a deliberate, sane floor for swing/trend detection — 12 one-
  minute bars is the minimum needed for the fractal-swing lookaround (n=2 each
  side) to produce a usable sequence at all.
- Bars come from two sources merged per-minute
  (`underlying_engine.py:150-187`): real feed 1m candles where the spot feed
  provides them, `INTERNAL_AGG_1m` bars built from the gate-selected
  underlying price otherwise. **A feed restart genuinely means a fresh
  12-minute wait** unless the spot feed itself backfills historical 1m
  candles on reconnect (an upstream behavior this repository cannot verify
  without live access — see `docs/SCHEMA.md`'s own note that the spot feed
  was observed with `ltp=null` in the one capture on file). This is a real,
  documented operational characteristic, not a bug to silently patch — doing
  so without verifying the live feed's actual backfill behavior would risk
  bootstrapping structure from fabricated data, which the audit's own
  constraints forbid.
- A data gap resets the *tail* used for warmup, never the whole day's data
  (`contiguous_tail` only discards segments **before** the last gap) — so a
  single 4-minute blip mid-session costs 12 bars of warmup, not the whole
  session. This is proportionate, not excessive.
- Session-level history (`previous_day_bars`) is used for level discovery
  (PDH/PDL/PDC/PDO) but deliberately **not** used to shortcut the live
  1-minute warmup — mixing daily and intraday timeframes for swing/trend
  detection would be a real correctness risk, not a safe optimization.

**Conclusion**: the warmup requirement is intentional and proportionate;
whether live feed restarts cause "excessive dead time" depends on upstream
feed behavior this repository has no live access to verify, so no change was
made.

## Fixes made

All of the following are **additive** — no existing field, weight, threshold,
confirmation count, or gate condition was changed or removed.

1. **`psygrid/diagnostics.py`** (new) — `SignalEvaluationTrace`: built from the
   real `ScoreResult` + `GateResult` for the cycle's best-scored candidate.
   Records, per `INDEPENDENT` confirmation: value, pass/fail, and (when it
   failed) *why* — quoting the owning feed's actual block/degrade reason when
   one exists. Also records conflicts, the score gap to threshold (only when
   confirmations/conflicts already passed, so it never misattributes a
   confirmation-gate rejection to "so close on score"), and whether a
   `SIGNAL`-grade candidate was separately rejected by risk/strike selection.
   Never influences `ScoringEngine`, `RiskEngine`, or `SignalStateManager` —
   it is read strictly after they've already decided.
2. **`IndexDecision.trace`** (`signal_engine.py`) — the trace is attached
   every cycle a candidate was evaluated, whether or not a signal resulted.
3. **`monitor.py`** — `Monitor.trace_lines()` renders the trace under WATCH
   and NO_TRADE: setup name/direction, score vs. threshold, confirmations
   N/M with PASS/MISSING lists (full per-confirmation breakdown with
   `--diagnostic`), the specific blocking reason, conflicts, and the
   near-miss point gap when applicable. Falls back to the previous terse
   reason line when no candidate was evaluated at all (a genuinely quiet
   market), so nothing is flooded when there is truly nothing to explain.
4. **`--diagnostic` CLI flag** (`run_engine.py`) — turns on the full
   per-confirmation breakdown in the terminal. This is presentation-only: it
   changes what `Monitor` prints and nothing else. `notify_new_signals` (the
   Telegram boundary) reads only `dec.signal`, which this flag never touches
   — structurally, not by an added check, so there is no code path by which
   `--diagnostic` (or WATCH, or NO_TRADE) can reach Telegram. Proven by
   `test_watch_and_no_trade_never_trigger_telegram_even_in_diagnostic_mode`.

## Findings, classified (Phase 12)

| finding | classification |
|---|---|
| Both `BUY CALL` and `BUY PUT` are reachable via the real production path under realistic simulated conditions | NO ISSUE (verified, not assumed) |
| `INDEPENDENT` confirmations exclude the price-action components that generate the candidate | INTENTIONAL SAFETY GATE |
| VWAP and "indicators" are one component, not two — no double-counted confirmation | NO ISSUE (verified) |
| Options/volume confirmations are unavailable for the first 1-3 polls after any (re)start | DATA AVAILABILITY PROBLEM (documented via "building history" messages; not fixable without inventing data) |
| Depth confirmation is doubled before clipping, so it saturates unusually easily | NO ISSUE for starvation (makes confirmation *easier*, not harder); noted for future calibration review only |
| A realistic solid-but-not-exceptional setup scores ~68-72, below `signal_threshold` (75) | INTENTIONAL SAFETY GATE — the threshold is calibrated to require genuine multi-source confluence, and is empirically reachable (77.4 in the passing breakout test) |
| Warmup (12 contiguous bars) resets after any >3-minute data gap | INTENTIONAL SAFETY GATE; proportionate (only the post-gap tail resets) |
| NO_TRADE/WATCH previously gave only 1-3 truncated reason strings, no confirmation breakdown, no near-miss quantification | OBSERVABILITY PROBLEM — **fixed** (`diagnostics.py`, `monitor.py`, `--diagnostic`) |
| A `SIGNAL`-grade candidate rejected only by risk/strike-selection was distinguishable only via the debug-only `dec.candidates` string list | OBSERVABILITY PROBLEM — **fixed** (`trace.risk_pass`/`risk_reason`) |
| No REAL BUG (a logic error making a direction or gate unconditionally unreachable) was found in this pass | — |

## Positive-path proof (Phases 6/7 acceptance criteria)

All of the following exercise `PsygridEngine.cycle()` — the real production
decision path — with no shortcut around any layer:

- `tests/test_scenarios.py::test_breakout_acceptance_emits_single_buy_call` —
  genuine CALL setup reaches `BUY CALL`, score >= `signal_threshold`.
- `tests/test_scenarios.py::test_mirror_scenario_emits_buy_put_with_same_quality` —
  the exact mirrored scenario reaches `BUY PUT` with matching quality.
- `tests/test_engine_io.py::test_live_signal_triggers_a_telegram_notification` —
  the accepted CALL signal reaches Telegram (end to end, including the
  notifier).
- `tests/test_engine_io.py::test_live_put_signal_triggers_a_telegram_notification` —
  same, for PUT (added by this audit).
- `tests/test_scenarios.py::test_chop_with_unavailable_confirmations_is_no_trade`,
  `test_bullish_depth_alone_never_buys` — negative controls: weak/insufficient
  setups correctly stay `NO_TRADE`.
- `tests/test_engine_io.py::test_watch_and_no_trade_never_trigger_telegram_even_in_diagnostic_mode` —
  WATCH, NO_TRADE, and full `--diagnostic` trace rendering never reach
  Telegram (added by this audit).
- `tests/test_diagnostics.py` (10 tests, added by this audit) — the trace
  itself: correct confirmation pass/fail split, correct blocking
  explanations, near-miss only reported when it's genuinely the sole
  remaining blocker, risk-rejection distinguished from confirmation-rejection.

None of these were written or modified to bypass any layer of the real
pipeline; the CALL/PUT/negative-control tests already existed before this
audit and are cited, not invented, as evidence.

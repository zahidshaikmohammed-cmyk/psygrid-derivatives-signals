"""Engine configuration.

Every tunable lives here. Defaults can be overridden with a JSON file
(``python run_engine.py --config my_config.json``) whose structure mirrors
``DEFAULTS``; only the keys you specify are changed.

None of the thresholds below were fitted to live or future data. They are
conservative starting points and must be recalibrated from logged outcomes
(see logs/) before any statistical meaning is attached to the scores.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

INDICES = ("NIFTY", "BANKNIFTY", "SENSEX")

DEFAULTS: dict[str, Any] = {
    "endpoints": {
        "base_url": "http://140.245.226.102:10000/public/",
        # file name = <prefix><suffix>.json, e.g. nifty-options.json
        "prefix": {"NIFTY": "nifty", "BANKNIFTY": "banknifty", "SENSEX": "sensex"},
        "feeds": {"spot": "", "options": "-options", "depth": "-depth",
                  "indicators": "-indicators", "futures": "-futures"},
        "timeout_seconds": 8.0,
        "retries": 1,
    },
    "poll_interval_seconds": 20,

    # ---------------------------------------------------------------- time
    "session": {
        "open": "09:15",
        "close": "15:30",
        "opening_range_minutes": 15,
        "no_new_entries_after": "15:00",
        "close_signals_at": "15:20",
        "weekdays_only": True,
    },

    # ---------------------------------------------------------- integrity
    "integrity": {
        # max age (seconds) of each feed's own timestamp vs reference time
        "max_age_seconds": {"spot_ltp": 20, "options": 30, "depth": 20,
                            "depth_quote": 30, "futures": 20},
        # indicator as_of is a bar START time; the bar closes 60s later
        "indicators_max_bar_age_seconds": 180,
        "spot_candle_max_age_seconds": 180,
        # cross-source consistency of the underlying price
        "max_underlying_divergence_pct": 0.30,
        "max_indicator_divergence_pct": 1.0,
        "max_futures_basis_pct": 3.0,
        "max_tick_jump_pct": 2.0,
        "max_clock_skew_seconds": 60,
        "accepted_market_status": ["OPEN"],
        "accepted_session_status": ["LIVE"],
        "accepted_feed_status": {
            "options": ["LIVE"], "depth": ["LIVE"], "futures": ["LIVE", "OK"],
            "indicators": ["OK"],
        },
    },

    # ------------------------------------------------ underlying / structure
    "structure": {
        "min_bars": 12,                # contiguous completed 1m bars before structure is trusted
        "max_gap_minutes": 3,          # bars further apart start a new segment
        "swing_lookaround": 2,         # fractal: N bars each side
        "avg_range_bars": 14,
        "momentum_lookback_bars": 5,
        "expansion_ratio": 1.3,
        "consolidation_bars": 12,
        "consolidation_max_ranges": 3.0,   # range of window <= k * avg bar range
        "aggregate_min_fill": 0.8,         # 5m bar needs >= 80% of its 1m bars
        "min_avg_range_pct": 0.01,         # floor for avg bar range (% of price)
    },

    # --------------------------------------------------------------- levels
    "levels": {
        "cluster_tolerance_pct": {"NIFTY": 0.05, "BANKNIFTY": 0.05, "SENSEX": 0.05},
        "min_zone_width_pct": 0.015,
        "round_number_steps": {
            "NIFTY": {"major": 100, "minor": 50},
            "BANKNIFTY": {"major": 500, "minor": 100},
            "SENSEX": {"major": 500, "minor": 100},
        },
        "round_number_range_pct": 1.0,
        "oi_window_pct": 3.0,          # option strikes considered for OI levels
        "oi_top_n": 3,
        "approach_ranges": 2.0,        # approaching = within k * avg bar range
        "reaction_ranges": 1.5,        # rejection = moved k * avg range away
        "acceptance_closes": 3,        # consecutive 1m closes beyond zone
        "failure_window_bars": 6,
        "retain_minutes": 120,
        "max_display_levels": 6,
        "tier1_min_strength": 60,
        "tier2_min_strength": 30,
        "weights": {
            "PDH": 22, "PDL": 22, "PDC": 16, "PDO": 10,
            "SESSION_HIGH": 14, "SESSION_LOW": 14,
            "OPENING_RANGE_HIGH": 12, "OPENING_RANGE_LOW": 12,
            "SWING_1m": 8, "SWING_5m": 12, "SWING_15m": 16, "SWING_FEED_HTF": 16,
            "REPEATED_REACTION_EACH": 5, "REPEATED_REACTION_MAX": 15,
            "VWAP": 10,
            "OI_CONCENTRATION_MAX": 18, "OI_CHANGE_MAX": 10,
            "SERVER_OI_LEVEL": 6, "MAX_PAIN": 4,
            "FUTURES": 8,
            "ROUND_MAJOR": 7, "ROUND_MINOR": 3,
            "LIQUIDITY_POOL": 8,
            "SUPPLY_DEMAND": 10,
            "CONFLUENCE_BONUS_EACH": 6, "CONFLUENCE_BONUS_MAX": 18,
            "REJECTION_BONUS_EACH": 4, "REJECTION_BONUS_MAX": 12,
            "STALE_SWING_FACTOR": 0.7,
        },
        "stale_swing_minutes": 120,
    },

    # ------------------------------------------------------------ liquidity
    "liquidity": {
        "sweep_lookback_bars": 10,
        "reclaim_bars": 2,
        "min_penetration_ranges": 0.15,
        "equal_level_ranges": 0.5,
        "max_sweep_age_bars": 6,
    },

    # -------------------------------------------------------------- setups
    "setups": {
        "max_event_age_seconds": 360,
        "max_chase_ranges": 2.5,       # do not chase further than k * avg range
        "min_room_ranges": 3.0,        # room to the next opposing major level
        "vwap_hold_closes": 2,
        "vwap_touch_ranges": 0.5,
        "invalidation_buffer_ranges": 0.35,
        "multi_factor_min_categories": 3,
        "multi_factor_min_strength": 70,
    },

    # ---------------------------------------------------------- options
    "options": {
        "strike_window": 6,            # strikes each side of ATM analysed
        "participation_polls": 4,      # polls used for volume / premium deltas
        "max_spread_pct": 3.0,
        "min_premium": {"NIFTY": 15, "BANKNIFTY": 40, "SENSEX": 20},
        "max_premium": {"NIFTY": 450, "BANKNIFTY": 1400, "SENSEX": 1400},
        "delta_band": [0.30, 0.70],
        "target_delta": 0.50,
        "max_strikes_from_atm": 4,
        "min_volume_vs_median": 0.10,
    },

    # ------------------------------------------------------------ futures
    "futures": {
        "momentum_polls": 4,
        "strong_ranges": 1.5,
        "confirm_ranges": 0.5,
    },

    # --------------------------------------------------------------- depth
    "depth": {
        "top_levels": 5,
        "strikes_each_side": 2,
        "strong_imbalance": 0.30,
        "weak_imbalance": 0.10,
    },

    # ------------------------------------------------------------- scoring
    "scoring": {
        "weights": {
            "structure": 14, "level": 16, "futures": 10, "momentum": 10,
            "volume": 8, "options": 12, "liquidity": 8, "depth": 8,
            "vwap_indicators": 8, "setup": 6, "data_quality": 6,
        },
        "conflict_penalty": 0.5,
        "signal_threshold": 75,
        "watch_threshold": 62,
        "min_independent_confirmations": 2,
        "confirm_threshold": 0.25,
        "strong_conflict": -0.5,
        "max_strong_conflicts": 1,
    },

    # ---------------------------------------------------------------- risk
    "risk": {
        "entry_band_pct": 2.0,
        "min_reward_risk": 1.2,
        "r_multiple_t1": 1.5,
        "r_multiple_t2": 2.5,
        "tick": 0.05,
    },

    # -------------------------------------------------------- signal state
    "signal_state": {
        "cooldown_seconds": 300,
        "requalify_score_jump": 10,
        "max_hold_minutes": {"MOMENTUM": 30, "REVERSAL": 45, "BREAKOUT": 40, "DEFAULT": 40},
    },

    # ------------------------------------------------------------- logging
    "logging": {
        "dir": "logs",
        "raw_snapshots": True,
        "raw_every_n_cycles": 1,
        "gzip_raw": True,
        "persist_observations": True,
    },

    "display": {"color": True, "clear_screen": True, "recent_events": 8},
}


class Config:
    """Thin attribute/dict wrapper around the nested defaults."""

    def __init__(self, data: dict[str, Any] | None = None):
        self._d = copy.deepcopy(DEFAULTS if data is None else data)

    def __getitem__(self, key: str) -> Any:
        return self._d[key]

    def get(self, *path: str, default: Any = None) -> Any:
        node: Any = self._d
        for p in path:
            if not isinstance(node, dict) or p not in node:
                return default
            node = node[p]
        return node

    def as_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._d)

    def per_index(self, section: str, key: str, index: str) -> Any:
        val = self._d[section][key]
        return val[index] if isinstance(val, dict) else val


def _deep_update(base: dict, override: dict, path: str = "") -> None:
    for k, v in override.items():
        if k not in base:
            raise KeyError(f"unknown config key: {path}{k}")
        if isinstance(v, dict) and isinstance(base[k], dict):
            _deep_update(base[k], v, f"{path}{k}.")
        else:
            base[k] = v


def load_config(path: str | Path | None = None) -> Config:
    data = copy.deepcopy(DEFAULTS)
    if path:
        _deep_update(data, json.loads(Path(path).read_text(encoding="utf-8")))
    return Config(data)

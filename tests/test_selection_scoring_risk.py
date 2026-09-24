
from psygrid.config import load_config
from psygrid.level_engine import LevelMap, Zone
from psygrid.option_chain_engine import OptionChainEngine
from psygrid.risk_engine import RiskEngine, option_estimate
from psygrid.schema_adapter import adapt_options
from psygrid.scoring_engine import Component, ScoringEngine
from psygrid.setup_engine import SetupCandidate
from psygrid.strike_selector import StrikeSelector

from sim import fixture


def chain_state(mut=None):
    p = fixture("nifty-options")
    if mut:
        mut(p)
    ch, _ = adapt_options(p, "NIFTY")
    return OptionChainEngine(load_config(), "NIFTY").analyze(ch, True, ch.underlying_ltp), ch


def test_strike_selection_real_chain_call_and_put():
    cs, ch = chain_state()
    c = StrikeSelector(load_config(), "NIFTY").select("CALL", cs, ch.underlying_ltp).selection
    p = StrikeSelector(load_config(), "NIFTY").select("PUT", cs, ch.underlying_ltp).selection
    assert c.option_type == "CE" and p.option_type == "PE"
    assert 0.3 <= abs(c.delta) <= 0.7 and 0.3 <= abs(p.delta) <= 0.7
    assert c.spread_pct < 1 and c.reasons and c.alternatives


def test_strike_selector_does_not_blindly_pick_atm():
    def widen_atm(p):
        for row in p["strikes"]:
            if row["strike"] == 23250.0:
                row["ce"]["top_ask_price"] = row["ce"]["top_bid_price"] * 1.02   # 2% spread
    cs, ch = chain_state(widen_atm)
    sel = StrikeSelector(load_config(), "NIFTY").select("CALL", cs, ch.underlying_ltp).selection
    assert sel.strike != 23250.0


def test_rejects_zero_and_invalid_quotes():
    def kill(p):
        for row in p["strikes"]:
            for side in ("ce", "pe"):
                row[side]["top_bid_price"] = 0
    cs, ch = chain_state(kill)
    res = StrikeSelector(load_config(), "NIFTY").select("CALL", cs, ch.underlying_ltp)
    assert res.selection is None and any("two-sided" in r for r in res.rejected)


def comps(values: dict):
    base = {k: Component(k, 0.0, "") for k in ("structure", "level", "futures", "momentum", "volume", "options",
                                                "liquidity", "depth", "vwap_indicators", "setup", "data_quality")}
    for k, v in values.items():
        base[k] = Component(k, v, "")
    return base


def test_scoring_signal_watch_and_no_trade():
    s = ScoringEngine(load_config())
    full = s.score(comps({k: 1.0 for k in ("structure", "level", "futures", "momentum", "volume", "options",
                                           "liquidity", "depth", "vwap_indicators", "setup", "data_quality")}))
    assert full.score == 100 and full.grade == "SIGNAL"
    weak = s.score(comps({"level": 0.5, "options": 0.3, "depth": 0.3, "setup": 0.5}))
    assert weak.grade == "NO_TRADE"


def test_unavailable_components_lower_score():
    s = ScoringEngine(load_config())
    all_ok = {k: 1.0 for k in ("structure", "level", "futures", "momentum", "volume", "options",
                               "liquidity", "depth", "vwap_indicators", "setup", "data_quality")}
    missing = dict(all_ok, futures=None, depth=None)
    assert s.score(comps(missing)).score < s.score(comps(all_ok)).score


def test_conflicting_signals_block():
    s = ScoringEngine(load_config())
    r = s.score(comps({"structure": 1, "level": 1, "momentum": 1, "volume": 1, "liquidity": 1, "setup": 1,
                       "data_quality": 1, "options": -0.8, "futures": -1.0, "depth": 0.5, "vwap_indicators": 0.5}))
    assert r.grade == "NO_TRADE" and "conflicting" in r.reasons[0]


def test_insufficient_independent_confirmation():
    s = ScoringEngine(load_config())
    r = s.score(comps({"structure": 1, "level": 1, "momentum": 1, "liquidity": 1, "setup": 1,
                       "data_quality": 1, "options": 0.3, "futures": None, "depth": None, "volume": None,
                       "vwap_indicators": None}))
    assert r.grade == "NO_TRADE" and "insufficient independent confirmation" in r.reasons[0]


def _sel():
    cs, ch = chain_state()
    return StrikeSelector(load_config(), "NIFTY").select("CALL", cs, ch.underlying_ltp).selection


def test_option_estimate_gamma_cushions_losses():
    sel = _sel()
    up, down = option_estimate(sel, 20), option_estimate(sel, -20)
    assert up > 0 > down and up > abs(down)


def test_risk_targets_from_levels_and_room_check():
    sel = _sel()
    z_far = Zone(id="R1", low=23300, high=23305, center=23302, tier=1, strength=80)
    z_far2 = Zone(id="R2", low=23380, high=23385, center=23382, tier=2, strength=50)
    cand = SetupCandidate("CALL", "BREAKOUT + ACCEPTANCE", None, 23220, 23210, 0.8, "x")
    plan, err = RiskEngine(load_config()).plan(cand, sel, LevelMap([z_far, z_far2], 23230), 23230, 200)
    assert plan and plan.underlying_t1 == 23300 and plan.underlying_t2 == 23380 and plan.reward_risk > 1.2
    assert plan.entry_low < sel.ltp < plan.entry_high and plan.option_t1 > sel.ltp > plan.option_invalidation
    z_near = Zone(id="R0", low=23240, high=23245, center=23242, tier=1, strength=80)
    plan, err = RiskEngine(load_config()).plan(cand, sel, LevelMap([z_near], 23230), 23230, 200)
    assert plan is None and "insufficient room" in err


def test_risk_r_multiples_when_no_levels_and_put_symmetry():
    sel = _sel()
    call = SetupCandidate("CALL", "MOMENTUM CONTINUATION", None, 0, 23210, 0.7, "x")
    put = SetupCandidate("PUT", "MOMENTUM CONTINUATION", None, 0, 23250, 0.7, "x")
    a, _ = RiskEngine(load_config()).plan(call, sel, LevelMap([], 23230), 23230, 200)
    b, _ = RiskEngine(load_config()).plan(put, sel, LevelMap([], 23230), 23230, 200)
    assert a.underlying_t1 - 23230 == 23230 - b.underlying_t1 == 30
    assert "R-multiples" in a.target_basis

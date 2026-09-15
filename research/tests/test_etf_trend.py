import numpy as np
import pandas as pd
import pytest

from research.engine import Plan, row_at, simulate
from research.etf_trend.data import dated_table, payable_total_return, total_return
from research.etf_trend.decompose import (
    attribution,
    defensive_spells,
    episode_events,
    equity_drawdowns,
)
from research.etf_trend.experiment import (
    ExperimentRun,
    frozen_plan,
    frozen_signals,
    reject_advanced_signals,
    run_fixed,
    switches,
)


def prices() -> pd.DataFrame:
    index = pd.bdate_range("2014-01-01", "2017-12-29")
    return pd.DataFrame(
        {
            "SPY": 100 * 1.0002 ** np.arange(len(index)),
            "DEFENSIVE": 100 * 1.00001 ** np.arange(len(index)),
        },
        index=index,
    )


def test_frozen_rules_use_calendar_month_ends_not_session_approximations():
    p = prices()
    signals = frozen_signals(p)
    levels = p.SPY.resample("ME").last()
    date = signals.index[15]
    row = row_at(signals, date)
    assert row.loc["momentum12"] == pytest.approx(levels.iloc[15] / levels.iloc[3] - 1)
    assert row.loc["sma10"] == pytest.approx(levels.iloc[6:16].mean())
    assert signals.iloc[:12].ABS12.isna().all()
    assert signals.iloc[:9].SMA10.isna().all()


def test_equal_threshold_is_defensive_for_both_exact_rules():
    p = prices() * 0 + 100
    signals = frozen_signals(p).dropna()
    assert (signals[["ABS12", "SMA10"]] == 0).all().all()


def test_new_account_enters_only_on_first_session_close_with_costs():
    p = prices()
    first = p.loc["2016":].index[0]
    result = run_fixed(p, "SPY", 20, "BIL")
    assert result.run.weights.loc[:"2015-12-31"].to_numpy().sum() == 0
    assert result.run.returns.loc[first] == pytest.approx(1 / 1.002 - 1)
    assert row_at(result.run.weights, first).loc["SPY"] == 1
    assert len(result.decisions) == 1
    assert result.decisions.execution_date.iloc[0] == first


def test_buy_and_hold_and_static_are_not_silently_same_rule():
    p = prices()
    buy = frozen_plan(p, "SPY")
    static = frozen_plan(p, "STATIC80")
    assert len(buy.weights.dropna()) == 1
    assert len(static.weights.dropna()) == 25
    assert (static.weights.dropna().SPY == 0.8).all()


def test_cash_stress_preserves_signal_but_removes_defensive_security_trades():
    p = prices()
    p.loc["2015-11":, "SPY"] *= 0.5
    funded = run_fixed(p, "ABS12", 20, "BIL")
    cash = run_fixed(p, "ABS12", 20, "ZERO_CASH")
    pd.testing.assert_series_equal(funded.run.weights.SPY, cash.run.weights.SPY)
    assert cash.run.weights.DEFENSIVE.sum() == 0
    assert cash.run.traded.sum() < funded.run.traded.sum()


def test_forward_one_month_signal_is_rejected_with_its_true_availability():
    outcomes = reject_advanced_signals(prices())
    assert len(outcomes) == 2
    assert all(row["future_month_signal"] == "REJECTED_LOOKAHEAD" for row in outcomes)


def test_no_parameters_or_cost_search_can_be_smuggled_into_fixed_runner():
    with pytest.raises(ValueError, match="No additional model"):
        frozen_plan(prices(), "SMA9")
    with pytest.raises(ValueError, match="Only the frozen"):
        run_fixed(prices(), "SMA10", 5, "BIL")


def test_time_in_equities_uses_return_earning_weights_not_same_close_targets():
    result = run_fixed(prices(), "SPY", 0, "BIL")
    info = switches(result.run)
    count = len(result.run.returns.loc["2016":])
    assert info["equity_state_switches_excluding_initial"] == 0
    assert info["initial_equity_entry"] == 1
    assert info["fraction_sessions_with_equity"] == pytest.approx((count - 1) / count)


def spell_run(cost: int = 0) -> tuple[ExperimentRun, pd.DataFrame]:
    index = pd.bdate_range("2016-01-01", periods=8)
    p = pd.DataFrame(
        {
            "SPY": [100.0, 100.0, 90.0, 60.0, 80.0, 110.0, 100.0, 110.0],
            "DEFENSIVE": np.repeat(100.0, 8),
        },
        index=index,
    )
    weights = pd.DataFrame(np.nan, index=index, columns=p.columns)
    weights.iloc[0] = [1.0, 0.0]
    weights.iloc[1] = [0.0, 1.0]
    weights.iloc[4] = [1.0, 0.0]
    plan = Plan(weights, pd.Series(index, index=index))
    run = simulate(p, plan, pd.Series(0.0, index=index), fee_bps=cost)
    decisions = weights.dropna().copy()
    decisions["execution_date"] = [index[1], index[2], index[5]]
    return ExperimentRun("ABS12", "BIL", cost, run, decisions), p


def test_drawdown_episodes_measure_high_to_low_and_mark_open_tail():
    index = pd.bdate_range("2016-01-01", periods=8)
    p = pd.Series([100.0, 90.0, 80.0, 105.0, 103.0, 90.0, 70.0, 75.0], index=index)
    episodes = equity_drawdowns(p)
    assert len(episodes) == 2
    assert episodes[0]["spy_drawdown"] == pytest.approx(-0.2)
    assert episodes[0]["recovery"] == str(index[3].date())
    assert episodes[1]["spy_drawdown"] == pytest.approx(70 / 105 - 1)
    assert episodes[1]["recovery"] is None
    assert episodes[1]["recovery_censored"] is True


def test_spell_counts_only_post_exit_returns_but_includes_exit_and_entry_fees():
    run, p = spell_run(20)
    spells = defensive_spells(run, p, start=p.index[1])
    assert len(spells) == 1
    spell = spells[0]
    assert spell["spy_return_while_defensive"] == pytest.approx(110 / 90 - 1)
    assert spell["post_exit_spy_loss_to_low"] == pytest.approx(60 / 90 - 1)
    assert spell["rebound_from_low_to_reentry"] == pytest.approx(110 / 60 - 1)
    assert spell["strategy_net_spell_return"] == pytest.approx(((1 - 0.002) / (1 + 0.002)) ** 2 - 1)
    assert spell["whipsaw"] is True
    assert spell["defensive_sessions"] == 3


def test_episode_decomposition_does_not_claim_pre_exit_loss_was_avoided():
    run, p = spell_run()
    episodes = equity_drawdowns(p.SPY)
    spells = defensive_spells(run, p, start=p.index[1])
    rows = episode_events(run, episodes, spells, p)
    assert rows[0]["strategy_return_peak_to_spy_trough"] == pytest.approx(-0.1)
    assert rows[0]["relative_loss_reduction_at_spy_trough"] == pytest.approx(0.3)
    assert rows[0]["spy_return_after_exit_until_trough_or_reentry"] == pytest.approx(60 / 90 - 1)


def test_pnl_and_matched_cost_attribution_reconcile_exactly():
    p = prices()
    p.loc["2015-10":, "SPY"] *= 0.7
    experiment = run_fixed(p, "ABS12", 20, "BIL")
    daily, totals = attribution(experiment, p)
    assert daily[
        ["spy_pnl", "defensive_total_return_pnl", "cost_pnl"]
    ].sum().sum() == pytest.approx(totals["total_dollar_pnl_per_initial_dollar"])
    assert totals["defensive_total_return_cagr_contribution"] > 0
    cash = run_fixed(p, "ABS12", 20, "ZERO_CASH")
    _, zero = attribution(cash, p)
    assert zero["defensive_dollar_pnl_per_initial_dollar"] == 0
    assert zero["defensive_total_return_cagr_contribution"] == pytest.approx(0)


def test_open_defensive_spell_is_right_censored_not_a_realized_whipsaw():
    run, p = spell_run()
    cutoff = p.index[4]
    shortened = ExperimentRun(
        run.model,
        run.defense,
        run.cost_bps,
        type(run.run)(
            run.run.returns.loc[:cutoff],
            run.run.weights.loc[:cutoff],
            run.run.traded.loc[:cutoff],
            run.run.costs.loc[:cutoff],
        ),
        run.decisions,
    )
    rows = defensive_spells(shortened, p.loc[:cutoff], start=p.index[1])
    assert rows[0]["open_right_censored"] is True
    assert rows[0]["reentry_execution"] is None
    assert rows[0]["whipsaw"] is False


def test_infinite_price_cannot_create_a_drawdown_episode():
    p = pd.Series([100.0, np.inf, 90.0], index=pd.bdate_range("2016-01-01", periods=3))
    with pytest.raises(ValueError):
        equity_drawdowns(p)


def test_changing_later_prices_cannot_change_an_earlier_calendar_month_signal():
    original = prices()
    changed = original.copy()
    changed.loc["2017-01-01":, "SPY"] *= 10
    for model in ("ABS12", "SMA10"):
        a = frozen_plan(original, model)
        b = frozen_plan(changed, model)
        pd.testing.assert_frame_equal(a.weights.loc[:"2016-12-31"], b.weights.loc[:"2016-12-31"])


def test_bil_reverse_split_is_not_an_investment_gain():
    index = pd.to_datetime(["2017-11-29", "2017-11-30", "2017-12-01"])
    nav = pd.Series([45.0, 90.0, 89.9], index=index)
    split = pd.Series([1.0, 0.5, 1.0], index=index)
    dividend = pd.Series([0.0, 0.0, 0.1], index=index)
    result = total_return(nav, dividend, split)
    assert result.total_return.to_numpy() == pytest.approx([0, 0, 0])
    assert result.total_return_level.to_numpy() == pytest.approx([100, 100, 100])


def test_dividend_is_receivable_until_payment_not_prematurely_reinvested():
    index = pd.bdate_range("2016-01-04", periods=3)
    nav = pd.Series([100.0, 99.0, 109.0], index=index)
    events = pd.DataFrame(
        {"distribution": [1.0], "PAYABLE DATE": [index[2]]}, index=pd.DatetimeIndex([index[1]])
    )
    result = payable_total_return(nav, events, pd.Series(1.0, index=index))
    assert result.total_return_level.to_numpy() == pytest.approx([100, 100, 110])
    assert result.unpaid_distribution_value.to_numpy() == pytest.approx([0, 1, 0])
    assert result.reinvested_units.iloc[1] == 1
    assert result.reinvested_units.iloc[2] == pytest.approx(1 + 1 / 109)


def test_issuer_footer_is_not_data_but_bad_numeric_date_is_not_ignored():
    frame = pd.DataFrame({"Date": ["04-Jan-2016", "issuer footer"], "NAV": [100.0, np.nan]})
    assert len(dated_table(frame, "NAV")) == 1
    frame.loc[1, "NAV"] = 50.0
    with pytest.raises(ValueError, match="numeric issuer observation"):
        dated_table(frame, "NAV")


def test_first_day_purchase_does_not_claim_prior_holder_distribution_or_split():
    index = pd.bdate_range("2017-11-30", periods=3)
    nav = pd.Series(90.0, index=index)
    splits = pd.Series([0.5, 1.0, 1.0], index=index)
    events = pd.DataFrame(
        {"distribution": [1.0], "PAYABLE DATE": [index[1]]}, index=pd.DatetimeIndex([index[0]])
    )
    result = payable_total_return(nav, events, splits)
    assert result.total_return_level.to_numpy() == pytest.approx([100, 100, 100])


def test_exit_after_crisis_trough_does_not_claim_the_owned_rebound_was_missed():
    experiment, p = spell_run()
    p["SPY"] = [100.0, 60.0, 80.0, 90.0, 100.0, 110.0, 100.0, 110.0]
    targets = experiment.decisions[["SPY", "DEFENSIVE"]].reindex(p.index)
    updated = simulate(
        p,
        Plan(targets, pd.Series(p.index, index=p.index)),
        pd.Series(0.0, index=p.index),
        fee_bps=0,
    )
    experiment = ExperimentRun("ABS12", "BIL", 0, updated, experiment.decisions)
    episodes = equity_drawdowns(p.SPY)
    spells = defensive_spells(experiment, p, start=p.index[1])
    rows = episode_events(experiment, episodes, spells, p)
    assert rows[0]["spy_return_after_exit_until_trough_or_reentry"] is None
    assert rows[0]["spy_rebound_while_defensive_after_trough"] == pytest.approx(110 / 80 - 1)
    assert rows[0]["full_spy_trough_to_reentry_rebound_not_all_missed"] == pytest.approx(
        110 / 60 - 1
    )

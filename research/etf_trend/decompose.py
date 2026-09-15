"""Auditable episode accounting for the two fixed binary SPY/defensive rules."""

import numpy as np
import pandas as pd

from research.engine import date_index, row_at
from research.etf_trend.experiment import START, ExperimentRun


def equity_drawdowns(spy: pd.Series, minimum: float = 0.10) -> list[dict]:
    if (
        not 0 < minimum < 1
        or spy.empty
        or not np.isfinite(spy.to_numpy()).all()
        or (spy <= 0).any()
    ):
        raise ValueError("Drawdown episodes require positive complete prices and a valid threshold")
    dates = date_index(spy.index)
    levels = spy.to_numpy(dtype=float)
    peak, trough = 0, 0
    episodes = []
    for i in range(1, len(levels)):
        if levels[i] >= levels[peak]:
            loss = levels[trough] / levels[peak] - 1
            if loss <= -minimum:
                episodes.append(
                    {
                        "peak": str(dates[peak].date()),
                        "trough": str(dates[trough].date()),
                        "recovery": str(dates[i].date()),
                        "spy_drawdown": float(loss),
                        "recovery_censored": False,
                    }
                )
            peak, trough = i, i
        elif levels[i] < levels[trough]:
            trough = i
    loss = levels[trough] / levels[peak] - 1
    if loss <= -minimum:
        episodes.append(
            {
                "peak": str(dates[peak].date()),
                "trough": str(dates[trough].date()),
                "recovery": None,
                "spy_drawdown": float(loss),
                "recovery_censored": True,
            }
        )
    return episodes


def defensive_spells(
    experiment: ExperimentRun, prices: pd.DataFrame, start: pd.Timestamp = START
) -> list[dict]:
    if experiment.model not in ("ABS12", "SMA10"):
        raise ValueError("A timing spell is defined only for the two binary trend rules")
    index = date_index(prices.index)
    returns = experiment.run.returns
    weights = experiment.run.weights
    decision_map: dict[pd.Timestamp, pd.Timestamp] = {}
    for decision in date_index(experiment.decisions.index):
        execution = experiment.decisions.execution_date.at[decision]
        if isinstance(execution, pd.Timestamp):
            decision_map[execution] = decision
    evaluation = date_index(prices.loc[start:].index)
    if not len(evaluation):
        raise ValueError("Empty spell evaluation period")
    first = evaluation[0]
    defensive = weights.SPY.loc[evaluation].lt(0.5).to_numpy()
    opened: pd.Timestamp | None = first if defensive[0] else None
    initial = bool(defensive[0])
    rows = []

    def close_spell(exit_date: pd.Timestamp, entry: pd.Timestamp | None, inherited: bool) -> None:
        end = entry if entry is not None else evaluation[-1]
        # The exit close executes after that day's prior SPY return. Include
        # its trade fee, not that prior return, in the spell's net return.
        ix = index[(index > exit_date) & (index <= end)]
        path = prices.SPY.loc[exit_date:end]
        trough = path.idxmin()
        if not isinstance(trough, pd.Timestamp):
            raise ValueError("A spell trough must identify a unique dated price")
        exit_price, end_price = float(path.iloc[0]), float(path.iloc[-1])
        spy_return = end_price / exit_price - 1
        defense_return = float(prices.DEFENSIVE.loc[end] / prices.DEFENSIVE.loc[exit_date] - 1)
        position = index.get_loc(exit_date)
        if not isinstance(position, (int, np.integer)):
            raise ValueError("A spell exit date must be unique")
        original_asset_returns = prices.pct_change(fill_method=None)
        previous = weights.iloc[int(position) - 1] if position > 0 else weights.iloc[0] * 0
        gross_exit = float((previous * row_at(original_asset_returns, exit_date).fillna(0)).sum())
        exit_retention = float((1 + returns.loc[exit_date]) / (1 + gross_exit))
        net_return = exit_retention * float(np.prod(1 + returns.loc[ix].to_numpy())) - 1
        sessions = len(ix)
        duration = (end - exit_date).days / 30.4375
        rows.append(
            {
                "model": experiment.model,
                "defense": experiment.defense,
                "cost_bps": experiment.cost_bps,
                "exit_decision": str(decision_map.get(exit_date, exit_date).date()),
                "exit_execution": str(exit_date.date()),
                "reentry_decision": (
                    str(decision_map[entry].date())
                    if entry is not None and entry in decision_map
                    else None
                ),
                "reentry_execution": str(entry.date()) if entry is not None else None,
                "end": str(end.date()),
                "started_defensive": inherited,
                "open_right_censored": entry is None,
                "defensive_sessions": sessions,
                "calendar_months": duration,
                "spy_return_while_defensive": spy_return,
                "defensive_etf_total_return_same_dates": defense_return,
                "strategy_net_spell_return": net_return,
                "net_relative_wealth_vs_staying_spy": (1 + net_return) / (1 + spy_return) - 1,
                "post_exit_spy_low_date": str(trough.date()),
                "post_exit_spy_loss_to_low": float(path.min() / exit_price - 1),
                "rebound_from_low_to_reentry": (
                    float(end_price / path.min() - 1) if entry is not None else None
                ),
                "whipsaw": bool(
                    not inherited
                    and entry is not None
                    and spy_return > 0
                    and net_return < spy_return
                ),
                "short_spell_at_most_3_calendar_months": bool(duration <= 3),
            }
        )

    for i in range(1, len(evaluation)):
        if defensive[i] and not defensive[i - 1]:
            opened, initial = evaluation[i], False
        elif not defensive[i] and defensive[i - 1] and opened is not None:
            close_spell(opened, evaluation[i], initial)
            opened = None
    if opened is not None:
        close_spell(opened, None, initial)
    return rows


def episode_events(
    experiment: ExperimentRun, episodes: list[dict], spells: list[dict], prices: pd.DataFrame
) -> list[dict]:
    result = []
    for episode in episodes:
        peak, trough = pd.Timestamp(episode["peak"]), pd.Timestamp(episode["trough"])
        end = pd.Timestamp(episode["recovery"]) if episode["recovery"] else prices.index[-1]
        relevant = [
            spell
            for spell in spells
            if pd.Timestamp(spell["exit_execution"]) <= end and pd.Timestamp(spell["end"]) >= peak
        ]
        net_path = (1 + experiment.run.returns.loc[peak:end]).cumprod()
        # Normalize at the already attained close of the peak.
        net_path = net_path / net_path.iloc[0]
        at_trough = float(net_path.loc[trough] - 1)
        for spell in relevant or [None]:
            after_exit_to_episode_trough = None
            rebound_missed = None
            full_trough_rebound = None
            if spell is not None:
                exit_date = pd.Timestamp(spell["exit_execution"])
                reentry = pd.Timestamp(spell["end"])
                if exit_date <= trough:
                    endpoint = min(trough, reentry)
                    after_exit_to_episode_trough = float(
                        prices.SPY.loc[endpoint] / prices.SPY.loc[exit_date] - 1
                    )
                if reentry >= trough and not spell["open_right_censored"]:
                    full_trough_rebound = float(
                        prices.SPY.loc[reentry] / prices.SPY.loc[trough] - 1
                    )
                    reference = max(trough, exit_date)
                    rebound_missed = float(prices.SPY.loc[reentry] / prices.SPY.loc[reference] - 1)
            result.append(
                {
                    "model": experiment.model,
                    "defense": experiment.defense,
                    "cost_bps": experiment.cost_bps,
                    **episode,
                    "strategy_return_peak_to_spy_trough": at_trough,
                    "relative_loss_reduction_at_spy_trough": at_trough - episode["spy_drawdown"],
                    "exit_execution": spell["exit_execution"] if spell else None,
                    "reentry_execution": spell["reentry_execution"] if spell else None,
                    "spy_return_after_exit_until_trough_or_reentry": after_exit_to_episode_trough,
                    "spy_rebound_while_defensive_after_trough": rebound_missed,
                    "full_spy_trough_to_reentry_rebound_not_all_missed": full_trough_rebound,
                    "no_defensive_spell_during_episode": spell is None,
                }
            )
    return result


def attribution(
    experiment: ExperimentRun, prices: pd.DataFrame, start: pd.Timestamp = START
) -> tuple[pd.DataFrame, dict]:
    returns = prices.pct_change(fill_method=None).fillna(0)
    ix = experiment.run.returns.loc[start:].index
    prior = experiment.run.weights.shift(1, fill_value=0).loc[ix]
    spy = prior.SPY * returns.SPY.loc[ix]
    defense = prior.DEFENSIVE * returns.DEFENSIVE.loc[ix]
    costs = experiment.run.costs.loc[ix]
    net = experiment.run.returns.loc[ix]
    if experiment.defense == "MATCHED_ZERO":
        defense = defense * 0
    if not np.allclose(spy + defense - costs, net, atol=1e-12):
        raise ArithmeticError("Component P&L does not reconcile with simulated wealth")
    previous_wealth = (1 + net).cumprod().shift(1, fill_value=1.0)
    pnl = pd.DataFrame(
        {
            "spy_pnl": previous_wealth * spy,
            "defensive_total_return_pnl": previous_wealth * defense,
            "cost_pnl": -previous_wealth * costs,
            "net_pnl": previous_wealth * net,
        }
    )
    if not np.isclose(pnl.net_pnl.sum(), np.prod(1 + net.to_numpy()) - 1, atol=1e-10):
        raise ArithmeticError("Cumulative component P&L fails terminal-wealth identity")
    gross = spy + defense
    retention = (1 + net) / (1 + gross)
    matched_zero_returns = (1 + spy) * retention - 1
    years = len(ix) / 252
    actual_cagr = float(np.prod(1 + net.to_numpy()) ** (1 / years) - 1)
    zero_cagr = float(np.prod(1 + matched_zero_returns.to_numpy()) ** (1 / years) - 1)
    return pnl, {
        "model": experiment.model,
        "cost_bps": experiment.cost_bps,
        "defense": experiment.defense,
        "spy_dollar_pnl_per_initial_dollar": float(pnl.spy_pnl.sum()),
        "defensive_dollar_pnl_per_initial_dollar": float(pnl.defensive_total_return_pnl.sum()),
        "cost_dollar_pnl_per_initial_dollar": float(pnl.cost_pnl.sum()),
        "total_dollar_pnl_per_initial_dollar": float(pnl.net_pnl.sum()),
        "cagr": actual_cagr,
        "matched_exposure_and_cost_zero_defense_cagr": zero_cagr,
        "defensive_total_return_cagr_contribution": actual_cagr - zero_cagr,
        "log_wealth_defensive_total_return_contribution": float(
            np.log1p(net).sum() - np.log1p(matched_zero_returns).sum()
        ),
        "attribution_note": (
            "Defensive total return includes yield, price, fund fees and reinvestment; "
            "Matched costs and exposures are attribution, not a new tradable strategy."
        ),
    }

"""Additional declared falsification: static exposure, delays, random timing and drawdown paths."""

import json

import numpy as np
import pandas as pd

from research.data import RESULTS, french_returns, verify_sources
from research.engine import (
    Plan,
    block_interval,
    constant_plan,
    date_index,
    simulate,
    summary,
    trend_plan,
)
from research.tournament import PERIODS, annual_drag, monthly_proxy_run


def quality_neighborhoods() -> None:
    ff = french_returns("ff_monthly")
    joint = french_returns("value_quality25")
    groups = {
        "single_high_value_high_profit": ["HiBM HiOP"],
        "top2_value_top2_profit": ["BM4 OP4", "BM4 OP5", "BM5 OP4", "HiBM HiOP"],
        "top3_value_top3_profit": [
            "BM3 OP3",
            "BM3 OP4",
            "BM3 OP5",
            "BM4 OP3",
            "BM4 OP4",
            "BM4 OP5",
            "BM5 OP3",
            "BM5 OP4",
            "HiBM HiOP",
        ],
    }
    output = []
    for name, members in groups.items():
        gross = joint[members].mean(axis=1)
        for drag in (0.005, 0.03):
            returns = annual_drag(gross, drag).to_frame("joint")
            run = monthly_proxy_run(returns, {"joint": 1.0}, ff.RF.loc[returns.index])
            for period, (start, end) in PERIODS.items():
                selected = run.returns.loc["1964-01-01":].loc[start:end]
                if len(selected) < 12:
                    continue
                benchmark = annual_drag(ff["Mkt-RF"] + ff.RF, 0.001).loc[selected.index]
                output.append(
                    {
                        "name": name,
                        "period": period,
                        "annual_drag": drag,
                        "size_controlled": False,
                        "purpose": "neighborhood falsification, not choosing the highest return",
                        **summary(selected, ff.RF.loc[selected.index], benchmark, 12),
                    }
                )
    pd.DataFrame(output).to_csv(RESULTS / "quality_neighborhoods.csv", index=False)


def main() -> None:
    verify_sources()
    quality_neighborhoods()
    ff = french_returns("ff_monthly").loc["1962-01-01":]
    rf = ff.RF
    prices = (1 + annual_drag(ff["Mkt-RF"] + rf, 0.001).to_frame("market")).cumprod()
    baseline = simulate(prices, constant_plan(prices, {"market": 1.0}, "every"), rf, fee_bps=5)
    outputs = []
    curves = {"market": baseline.returns}
    training_cutoff = "1999-12-31"
    for kind, lookback in (("sma", 10), ("absolute", 12)):
        name = f"{kind}{lookback}"
        plan = trend_plan(prices, kind=kind, lookback=lookback, frequency="every")
        run = simulate(prices, plan, rf, fee_bps=5)
        exposure = float(run.weights.loc["1964-01-01":training_cutoff].sum(axis=1).mean())
        static = simulate(
            prices, constant_plan(prices, {"market": exposure}, "every"), rf, fee_bps=5
        )
        curves[name] = run.returns
        curves[name + "_static"] = static.returns
        for period, (start, end) in PERIODS.items():
            ix = run.returns.loc["1964-01-01":].loc[start:end].index
            if len(ix) < 12:
                continue
            for label, r in (("trend", run.returns), ("training_exposure_static", static.returns)):
                metrics = summary(r.loc[ix], rf.loc[ix], baseline.returns.loc[ix], 12)
                outputs.append(
                    {
                        "rule": name,
                        "comparator": label,
                        "period": period,
                        "static_exposure_from_1964_1999_only": exposure,
                        **metrics,
                    }
                )
            difference = run.returns.loc[ix] - static.returns.loc[ix]
            if period in ("full", "2010_2019", "2020_onward") and len(ix) >= 24:
                low, high = block_interval(difference)
                outputs.append(
                    {
                        "rule": name,
                        "comparator": "paired_block_mean_excess_vs_static",
                        "period": period,
                        "annual_mean_excess": float(difference.mean() * 12),
                        "lower_95": low,
                        "upper_95": high,
                    }
                )
        # Shift the entire binary allocation sequence by fixed offsets, keeping spell lengths.
        # This is a falsification distribution, NOT valid traded alternatives.
        weights = plan.weights.fillna(0).loc["1964-01-01":]
        empirical = summary(
            run.returns.loc[weights.index],
            rf.loc[weights.index],
            baseline.returns.loc[weights.index],
            12,
        )
        controls = []
        for offset in range(24, len(weights) - 24, 12):
            rolled = pd.DataFrame(
                np.roll(weights.to_numpy(), offset, axis=0),
                index=weights.index,
                columns=weights.columns,
            )
            invalid = Plan(rolled, pd.Series(weights.index, index=weights.index))
            placebo = simulate(prices.loc[weights.index], invalid, rf.loc[weights.index], fee_bps=5)
            metrics = summary(
                placebo.returns, rf.loc[weights.index], baseline.returns.loc[weights.index], 12
            )
            controls.append(metrics)
        controls_frame = pd.DataFrame(controls)
        outputs.append(
            {
                "rule": name,
                "comparator": "circular_shift_falsification_only",
                "control_count": len(controls),
                "real_sharpe": empirical["sharpe"],
                "real_max_drawdown": empirical["max_drawdown"],
                "shifted_sharpe_median": float(controls_frame.sharpe.median()),
                "shifted_sharpe_95": float(controls_frame.sharpe.quantile(0.95)),
                "fraction_shifted_sharpe_at_least_real": float(
                    (controls_frame.sharpe >= empirical["sharpe"]).mean()
                ),
                "shifted_drawdown_median": float(controls_frame.max_drawdown.median()),
                "invalid_for_portfolio_selection": True,
            }
        )
    (RESULTS / "exposure_falsification.json").write_text(json.dumps(outputs, indent=2) + "\n")
    pd.DataFrame(curves).loc["1964-01-01":].to_csv(
        RESULTS / "exposure_monthly_returns.csv", float_format="%.10g"
    )
    # Fixed cut dates compare the cumulative wealth difference that crises contribute.
    comparison = pd.DataFrame(curves).loc["1964-01-01":]
    relative = pd.DataFrame(np.log1p(comparison)).sub(np.log1p(comparison.market), axis=0)
    attribution = []
    for year, frame in relative.groupby(date_index(relative.index).year):
        for name in ("sma10", "absolute12"):
            attribution.append(
                {"year": int(year), "rule": name, "log_wealth_excess": float(frame[name].sum())}
            )
    pd.DataFrame(attribution).to_csv(RESULTS / "crisis_attribution.csv", index=False)
    print(json.dumps({"exposure_and_placebo_comparisons": len(outputs), "retrospective": True}))


if __name__ == "__main__":
    main()

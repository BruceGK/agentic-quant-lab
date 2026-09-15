"""Run the predeclared exploratory comparisons; no strategy/parameter is chosen by Sharpe."""

import json
from dataclasses import asdict, dataclass
from itertools import product

import numpy as np
import pandas as pd

from research.data import CACHE, RESULTS, STOCK_SECTORS, french_returns, price_panel, read_prices
from research.engine import (
    Run,
    block_interval,
    column,
    constant_plan,
    date_index,
    holding_spells,
    momentum_plan,
    monthly,
    simulate,
    summary,
    trend_plan,
)

PERIODS = {
    "full": (None, None),
    "pre2000": ("1964-01-01", "1999-12-31"),
    "2000_2007": ("2000-01-01", "2007-12-31"),
    "2008_2009": ("2008-01-01", "2009-12-31"),
    "2010_2019": ("2010-01-01", "2019-12-31"),
    "2020_onward": ("2020-01-01", None),
    "dotcom": ("2000-01-01", "2002-12-31"),
    "gfc": ("2008-01-01", "2008-12-31"),
    "rebound2009": ("2009-01-01", "2009-12-31"),
    "covid2020": ("2020-01-01", "2020-12-31"),
    "inflation2022": ("2022-01-01", "2022-12-31"),
    "2023_2025": ("2023-01-01", "2025-12-31"),
}


@dataclass(frozen=True)
class Spec:
    name: str
    family: str
    dataset: str
    scenario: str
    benchmark: str
    parameter: str
    timing: str
    data_quality: str = "EXPLORATORY"
    tradable_holdings_known: bool = True


class Results:
    def __init__(self):
        self.metrics: list[dict] = []
        self.curves: dict[str, pd.Series] = {}
        self.run_metadata: list[dict] = []
        self.robustness: list[dict] = []

    def add(
        self,
        run: Run,
        spec: Spec,
        cash: pd.Series,
        benchmark: pd.Series,
        ppy: int,
        start: str,
        *,
        keep_curve: bool = False,
    ) -> None:
        returns = run.returns.loc[start:]
        if returns.empty:
            raise ValueError("Empty evaluation period")
        for period, (left, right) in PERIODS.items():
            selected = returns.loc[left:right]
            if len(selected) < ppy // 2:
                continue
            ix = selected.index
            values = summary(selected, cash.loc[ix], benchmark.loc[ix], ppy)
            years = len(selected) / ppy
            w = run.weights.loc[ix]
            values |= {
                "annual_traded_notional": float(run.traded.loc[ix].sum() / years),
                "annual_one_way_equivalent_turnover": float(run.traded.loc[ix].sum() / years / 2),
                "annual_transaction_cost_fraction": float(run.costs.loc[ix].sum() / years),
                "mean_invested_fraction": float(w.sum(axis=1).mean()),
                "mean_holdings": float((w > 1e-10).sum(axis=1).mean())
                if spec.tradable_holdings_known
                else None,
                **(holding_spells(w, ppy) if spec.tradable_holdings_known else {}),
            }
            self.metrics.append(asdict(spec) | {"period": period} | values)
        self.run_metadata.append(
            asdict(spec) | {"evaluated_start": start, "observations": len(returns)}
        )
        if keep_curve:
            self.curves[spec.name] = monthly(returns, ppy)
            excess = monthly(returns, ppy) - monthly(benchmark.loc[returns.index], ppy)
            if len(excess) >= 24:
                low, high = block_interval(excess)
                self.robustness.append(
                    {
                        "name": spec.name,
                        "test": "paired_12m_block_bootstrap_mean_excess",
                        "mean_annual_excess": float(excess.mean() * 12),
                        "lower_95": low,
                        "upper_95": high,
                        "multiple_testing_adjusted": False,
                    }
                )

    def save(self) -> None:
        RESULTS.mkdir(exist_ok=True)
        pd.DataFrame(self.metrics).to_csv(
            RESULTS / "tournament.csv", index=False, float_format="%.9g"
        )
        pd.DataFrame(self.curves).to_csv(RESULTS / "monthly_returns.csv", float_format="%.10g")
        (RESULTS / "run_registry.json").write_text(json.dumps(self.run_metadata, indent=2) + "\n")
        (RESULTS / "robustness.json").write_text(json.dumps(self.robustness, indent=2) + "\n")


def monthly_proxy_run(returns: pd.DataFrame, allocation: dict[str, float], rf: pd.Series) -> Run:
    prices = (1 + returns).cumprod()
    return simulate(prices, constant_plan(prices, allocation, "every"), rf, fee_bps=5, delay=1)


def annual_drag(returns: pd.Series, drag: float) -> pd.Series:
    return (1 + returns) * (1 - drag) ** (1 / 12) - 1


def long_horizon(results: Results) -> None:
    factors = french_returns("ff_monthly")
    rf = factors.RF
    market = factors["Mkt-RF"] + rf
    mnet = annual_drag(market, 0.001)
    prices = (1 + mnet.to_frame("market")).cumprod()
    benchmark = simulate(prices, constant_plan(prices, {"market": 1.0}, "every"), rf, fee_bps=5)
    results.add(
        benchmark,
        Spec(
            "market_proxy",
            "benchmark",
            "French monthly",
            "base",
            "French market, not SPY",
            "all",
            "static",
        ),
        rf,
        benchmark.returns,
        12,
        "1964-01-01",
        keep_curve=True,
    )
    for kind, months, fee, cash_mode in product(
        ("sma", "absolute"), (6, 9, 10, 12), (2, 5, 20), ("rf", "zero")
    ):
        cash = rf if cash_mode == "rf" else rf * 0
        plan = trend_plan(prices, kind=kind, lookback=months, frequency="every")
        run = simulate(prices, plan, cash, fee_bps=fee)
        name = f"market_{kind}{months}_{cash_mode}_{fee}bps"
        results.add(
            run,
            Spec(
                name,
                "trend",
                "French monthly",
                f"{fee}bps_{cash_mode}",
                "French market, not SPY",
                f"{kind}/{months}",
                "one full month execution delay",
            ),
            rf,
            benchmark.returns,
            12,
            "1964-01-01",
            keep_curve=fee == 5
            and cash_mode == "rf"
            and (kind, months) in (("sma", 10), ("absolute", 12)),
        )
    for kind in ("sma", "absolute"):
        months = 10 if kind == "sma" else 12
        for delay, vol_target in ((2, None), (1, 0.10)):
            plan = trend_plan(
                prices,
                kind=kind,
                lookback=months,
                frequency="every",
                vol_target=vol_target,
                periods_per_year=12,
            )
            run = simulate(prices, plan, rf, fee_bps=5, delay=delay)
            name = f"market_{kind}{months}_delay{delay}_vol{vol_target}"
            results.add(
                run,
                Spec(
                    name,
                    "trend",
                    "French monthly",
                    "base",
                    "French market, not SPY",
                    f"delay={delay},vol={vol_target}",
                    "monthly lag",
                ),
                rf,
                benchmark.returns,
                12,
                "1964-01-01",
                keep_curve=True,
            )
    # No same-close result is allowed into the engine. This diagnostic is explicitly invalid.
    optimistic = prices.market.gt(prices.market.rolling(10).mean()).shift(1).fillna(False)
    optimistic_returns = mnet.where(optimistic, rf).loc["1964-01-01":]
    invalid = summary(
        optimistic_returns,
        rf.loc[optimistic_returns.index],
        benchmark.returns.loc[optimistic_returns.index],
        12,
    )
    results.robustness.append(
        {
            "name": "SMA10_same_close",
            "test": "optimistic_timing_INVALID_FOR_IMPLEMENTATION",
            **invalid,
        }
    )
    momentum = french_returns("momentum6")
    quality = french_returns("profitability6")
    value = french_returns("value6")
    joint = french_returns("value_quality25")
    sleeves = pd.DataFrame(
        {
            "long_momentum": momentum["BIG HiPRIOR"],
            "long_losers_diagnostic": momentum["BIG LoPRIOR"],
            "small_momentum_diagnostic": momentum["SMALL HiPRIOR"],
            "long_quality": quality["BIG HiOP"],
            "low_quality_diagnostic": quality["BIG LoOP"],
            "long_value": value["BIG HiBM"],
            "joint_value_quality": joint[["BM4 OP4", "BM4 OP5", "BM5 OP4", "HiBM HiOP"]].mean(
                axis=1
            ),
        }
    ).dropna()
    for name in map(str, sleeves.columns):
        base_drag = 0.015 if "momentum" in name or "losers" in name else 0.005
        for drag in sorted({0.0, base_drag, 0.03, 0.06}):
            returns = annual_drag(column(sleeves, str(name)), drag).to_frame(str(name))
            run = monthly_proxy_run(returns, {name: 1.0}, rf.loc[returns.index])
            spec = Spec(
                f"{name}_drag{drag:g}",
                "academic long leg",
                "French portfolio, not ETF",
                "base" if drag == base_drag else f"annual_drag_{drag:g}",
                "French market, not SPY",
                name,
                "provider PIT convention; revised vintage",
                tradable_holdings_known=False,
            )
            results.add(
                run, spec, rf, benchmark.returns, 12, "1964-01-01", keep_curve=drag == base_drag
            )
            # Underlying turnover/costs are not recoverable from aggregate basket returns.
            for row in results.metrics:
                if row["name"] == spec.name:
                    row["assumed_annual_internal_drag"] = drag
                    row["annual_traded_notional"] = None
                    row["annual_one_way_equivalent_turnover"] = None
                    row["annual_transaction_cost_fraction"] = None


def etf_experiments(results: Results) -> None:
    prices, _, _ = price_panel("etfs")
    factors = french_returns("ff_daily")
    for universe in (("SPY",), ("SPY", "AGG")):
        selected = pd.DataFrame(prices[list(universe)])
        start = max(date_index(column(selected, name).dropna().index)[0] for name in universe)
        end = min(
            pd.Timestamp("2015-12-31"),
            min(date_index(column(selected, name).dropna().index)[-1] for name in universe),
        )
        p = selected.loc[start:end]
        if p.isna().any().any():
            raise ValueError("ETF snapshot contains internal gaps")
        rf = factors.RF.reindex(p.index)
        spy = p["SPY"].pct_change(fill_method=None).fillna(0)
        evaluated = str(p.index[253].date())
        tag = "_".join(universe)
        base = simulate(
            p, constant_plan(p, {symbol: 1 / len(universe) for symbol in universe}), rf, fee_bps=5
        )
        results.add(
            base,
            Spec(
                f"{tag}_hold",
                "benchmark",
                "actual ETF snapshot",
                "base",
                "SPY",
                "equal assets",
                "next session close",
            ),
            rf,
            spy,
            252,
            evaluated,
            keep_curve=True,
        )
        for kind, lookback, fee, mode in product(
            ("sma", "absolute"), (126, 189, 210, 252), (2, 5, 20), ("rf", "zero")
        ):
            plan = trend_plan(p, kind=kind, lookback=lookback)
            run = simulate(p, plan, rf if mode == "rf" else rf * 0, fee_bps=fee)
            name = f"{tag}_{kind}{lookback}_{mode}_{fee}bps"
            results.add(
                run,
                Spec(
                    name,
                    "ETF trend",
                    "actual ETF snapshot",
                    f"{fee}bps_{mode}",
                    "SPY",
                    f"{kind}/{lookback}",
                    "next session close",
                ),
                rf,
                spy,
                252,
                evaluated,
                keep_curve=fee == 5
                and mode == "rf"
                and (kind, lookback) in (("sma", 210), ("absolute", 252)),
            )
        for kind, vol, delay in (("dual", None, 1), ("sma", 0.10, 1), ("sma", None, 2)):
            run = simulate(
                p,
                trend_plan(p, kind=kind, lookback=210, vol_target=vol),
                rf,
                fee_bps=5,
                delay=delay,
            )
            name = f"{tag}_{kind}_vol{vol}_delay{delay}"
            results.add(
                run,
                Spec(
                    name,
                    "ETF trend",
                    "actual ETF snapshot",
                    "base",
                    "SPY",
                    f"{kind},vol={vol},delay={delay}",
                    "lagged close",
                ),
                rf,
                spy,
                252,
                evaluated,
                keep_curve=True,
            )


def stock_experiments(results: Results) -> None:
    all_prices, raw, volume = price_panel("stocks")
    # Source audit, not performance selection: eight missing-date rows all precede 2003.
    prices = all_prices.loc["2003-01-01":"2012-08-31"]
    if prices.isna().any().any():
        raise ValueError("Convenience stock panel still has missing session prices")
    raw, volume = raw.loc[prices.index], volume.loc[prices.index]
    rf = french_returns("ff_daily").RF.reindex(prices.index)
    spy = read_prices(CACHE / "etfs/SPY.csv").adj_close.reindex(prices.index).pct_change().fillna(0)
    evaluated = str(prices.index[253].date())
    equal = simulate(
        prices,
        constant_plan(prices, dict.fromkeys(prices.columns, 1 / len(prices.columns))),
        rf,
        fee_bps=15,
    )
    results.add(
        equal,
        Spec(
            "stocks_equal_weight",
            "benchmark",
            "survivor stock snapshot",
            "base",
            "SPY",
            "70 fixed survivors",
            "next session close",
        ),
        rf,
        spy,
        252,
        evaluated,
        keep_curve=True,
    )
    plan_cache = {}
    for horizons, breadth, frequency, minimum in product(
        ((126,), (189,), (252,), (126, 189, 252)),
        (10, 20, 30, 50),
        ("monthly", "biweekly"),
        (10_000_000, 50_000_000, 100_000_000),
    ):
        key = (horizons, breadth, frequency, minimum)
        plan_cache[key] = momentum_plan(
            prices,
            raw,
            volume,
            lookbacks=horizons,
            breadth=breadth,
            frequency=frequency,
            minimum_dollars=minimum,
        )
        for fee in (5, 15, 50):
            run = simulate(prices, plan_cache[key], rf, fee_bps=fee)
            name = (
                f"stocks_mom{'-'.join(map(str, horizons))}_n{breadth}"
                f"_{frequency}_liq{minimum:g}_{fee}bps"
            )
            central = key == ((252,), 20, "monthly", 50_000_000) and fee == 15
            results.add(
                run,
                Spec(
                    name,
                    "stock momentum",
                    "survivor stock snapshot",
                    f"{fee}bps",
                    "SPY",
                    f"{horizons};n={breadth};{frequency};liq={minimum}",
                    "next session close",
                ),
                rf,
                spy,
                252,
                evaluated,
                keep_curve=central,
            )
            if central:
                w = run.weights.loc[evaluated:]
                sector_weights = w.T.groupby(pd.Series(STOCK_SECTORS).reindex(w.columns)).sum().T
                rvol = prices.pct_change(fill_method=None).rolling(63).std().shift(1)
                vol_load = w * rvol.loc[w.index]
                fraction = vol_load.div(vol_load.sum(axis=1).replace(0, np.nan), axis=0)
                results.robustness.append(
                    {
                        "name": name,
                        "test": "concentration",
                        "max_sector_weight": float(sector_weights.max(axis=1).max()),
                        "mean_largest_sector_weight": float(sector_weights.max(axis=1).mean()),
                        "mean_top5_vol_load": float(
                            np.sort(fraction.fillna(0).to_numpy(), axis=1)[:, -5:]
                            .sum(axis=1)
                            .mean()
                        ),
                        "sector_classification": "static modern labels, not historical GICS",
                    }
                )
                # Aggregate each net return separately, not a compounded daily difference.
                difference = monthly(run.returns.loc[evaluated:], 252) - monthly(
                    equal.returns.loc[evaluated:], 252
                )
                low, high = block_interval(difference)
                results.robustness.append(
                    {
                        "name": name,
                        "test": "paired_excess_vs_equal_universe",
                        "mean_annual_excess": float(difference.mean() * 12),
                        "lower_95": low,
                        "upper_95": high,
                    }
                )
    for label, buffer, cap, delay in (
        ("buffer1.5", 1.5, None, 1),
        ("sector30", 1.0, 0.30, 1),
        ("delay2", 1.0, None, 2),
    ):
        plan = momentum_plan(
            prices, raw, volume, buffer=buffer, sector_cap=cap, sectors=STOCK_SECTORS
        )
        run = simulate(prices, plan, rf, fee_bps=15, delay=delay)
        results.add(
            run,
            Spec(
                f"stocks_{label}",
                "stock momentum",
                "survivor stock snapshot",
                "base",
                "SPY",
                label,
                "next-session or delayed close",
            ),
            rf,
            spy,
            252,
            evaluated,
            keep_curve=True,
        )
    random_rows = []
    for seed in range(40):
        plan = momentum_plan(prices, raw, volume, random_seed=seed)
        run = simulate(prices, plan, rf, fee_bps=15)
        ix = run.returns.loc[evaluated:].index
        metric = summary(run.returns.loc[ix], rf.loc[ix], spy.loc[ix], 252)
        random_rows.append({"seed": seed, **metric})
    pd.DataFrame(random_rows).to_csv(
        RESULTS / "random_portfolios.csv", index=False, float_format="%.9g"
    )
    # Dollar sizing at one historical date: a feasibility check, not a rounding backtest.
    date = plan_cache[((252,), 20, "monthly", 50_000_000)].weights.dropna().index[-1]
    sizing = []
    for capital, breadth in product((1000, 10000, 50000), (10, 20, 30, 50)):
        target = plan_cache[((252,), breadth, "monthly", 50_000_000)].weights.dropna().iloc[-1]
        dollars = target * capital
        whole = np.floor(dollars / raw.loc[date]) * raw.loc[date]
        sizing.append(
            {
                "capital": capital,
                "target_breadth": breadth,
                "date": str(date.date()),
                "fractional_names": int((target > 0).sum()),
                "whole_share_names": int((whole > 0).sum()),
                "uninvested_due_to_rounding_fraction": float(1 - whole.sum() / capital),
                "before_costs_and_not_an_execution_simulation": True,
            }
        )
    (RESULTS / "capital_sizing.json").write_text(json.dumps(sizing, indent=2) + "\n")


def complementarity(results: Results) -> None:
    names = [
        "market_proxy",
        "market_sma10_rf_5bps",
        "market_absolute12_rf_5bps",
        "long_momentum_drag0.015",
        "long_quality_drag0.005",
        "long_value_drag0.005",
        "joint_value_quality_drag0.005",
    ]
    aligned = pd.DataFrame({name: results.curves[name] for name in names}).dropna()
    aligned.corr().to_csv(RESULTS / "correlations.csv", float_format="%.8g")
    rf = french_returns("ff_monthly").RF.loc[aligned.index]
    for name, members in (
        ("mix_trend_momentum", ["market_sma10_rf_5bps", "long_momentum_drag0.015"]),
        ("mix_momentum_quality", ["long_momentum_drag0.015", "long_quality_drag0.005"]),
        (
            "mix_trend_momentum_quality",
            ["market_sma10_rf_5bps", "long_momentum_drag0.015", "long_quality_drag0.005"],
        ),
        (
            "mix_trend_momentum_value",
            ["market_sma10_rf_5bps", "long_momentum_drag0.015", "long_value_drag0.005"],
        ),
    ):
        data = aligned[members]
        average = data.mean(axis=1)
        drift = (1 + data).div(1 + average, axis=0) / len(members)
        turnover = (drift - 1 / len(members)).abs().sum(axis=1)
        r = (1 + average) * (1 - turnover * 0.0005) - 1
        run = Run(
            r,
            pd.DataFrame(1 / len(members), index=r.index, columns=members),
            turnover,
            (1 + average) * turnover * 0.0005,
        )
        results.add(
            run,
            Spec(
                name,
                "equal sleeve mix",
                "monthly research proxies",
                "net base",
                "French market, not SPY",
                "+".join(members),
                "fixed monthly mix; underlying strategies already lagged",
                tradable_holdings_known=False,
            ),
            rf,
            aligned["market_proxy"],
            12,
            "1964-01-01",
            keep_curve=True,
        )
    for name in names[1:] + ["mix_trend_momentum_quality"]:
        r = results.curves[name].reindex(aligned.index)
        benchmark = aligned.market_proxy
        for label, mask in (
            (
                "exclude_2000_2002_2008_2009_2020_2022",
                ~date_index(aligned.index).year.isin([2000, 2001, 2002, 2008, 2009, 2020, 2022]),
            ),
            ("bull_months", benchmark >= 0),
            ("bear_months", benchmark < 0),
            ("lagged_vol_above20", benchmark.rolling(12).std().shift(1) * np.sqrt(12) > 0.20),
            ("lagged_vol_at_most20", benchmark.rolling(12).std().shift(1) * np.sqrt(12) <= 0.20),
        ):
            selected = r.loc[mask]
            results.robustness.append(
                {
                    "name": name,
                    "test": label,
                    "months": len(selected),
                    "mean_annual_excess": float(
                        (selected - benchmark.loc[selected.index]).mean() * 12
                    ),
                    "annualized_volatility": float(selected.std() * np.sqrt(12)),
                    "descriptive_noncontiguous_not_a_tradable_backtest": True,
                }
            )


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    results = Results()
    print("Running predeclared long-horizon market and academic-sleeve tests", flush=True)
    long_horizon(results)
    print("Running actual ETF snapshot trend tests", flush=True)
    etf_experiments(results)
    print("Running survivor-biased stock implementation sensitivity tests", flush=True)
    stock_experiments(results)
    print("Running fixed sleeve mixes and falsification summaries", flush=True)
    complementarity(results)
    results.save()
    print(
        json.dumps(
            {
                "runs": len(results.run_metadata),
                "metric_rows": len(results.metrics),
                "monthly_curves": len(results.curves),
                "classification": "EXPLORATORY",
            }
        )
    )


if __name__ == "__main__":
    main()

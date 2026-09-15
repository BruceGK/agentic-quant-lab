"""Standardized candidate cards and compact comparison tables; never rank by a fitted Sharpe."""

import json

import pandas as pd

from research.data import RESULTS

CANDIDATES = [
    {
        "candidate": "ETF absolute momentum",
        "rank": "BUILD FIRST",
        "representative": "SPY_absolute252_rf_5bps",
        "description": "Equity ETF with positive 252-session return; otherwise cash/RF",
        "confidence": "Medium for defensive purpose; low for excess return",
        "complexity": "Low",
        "agentic_upside": "Replication and failure-regime audits, not discretionary sizing",
    },
    {
        "candidate": "ETF moving-average trend",
        "rank": "BUILD FIRST comparator",
        "representative": "SPY_sma210_rf_5bps",
        "description": "Single equity ETF above its 210-session SMA; monthly decisions",
        "confidence": "Medium for defensive purpose; low for excess return",
        "complexity": "Low",
        "agentic_upside": "Falsify timing, cash-yield and rebound assumptions",
    },
    {
        "candidate": "Quality-oriented diversifying sleeve",
        "rank": "BUILD SECOND paper comparison",
        "representative": "long_quality_drag0.005",
        "description": "French large robust-profitability basket; ETF implementation untested",
        "confidence": "Medium-low; proxy only, market-correlated",
        "complexity": "Low-medium for ETF; high for custom PIT stocks",
        "agentic_upside": "Audit accounting definitions, restatements and valuation crowding",
    },
    {
        "candidate": "Cross-sectional stock momentum",
        "rank": "RESEARCH MORE",
        "representative": "stocks_mom252_n20_monthly_liq5e+07_15bps",
        "description": "12-1 ranking, 20 stocks, monthly, $50m trailing-dollar-volume screen",
        "confidence": "Low: survivor panel and weak equal-universe comparison",
        "complexity": "Medium",
        "agentic_upside": "Concentration/turnover degradation tests and data anomaly review",
    },
    {
        "candidate": "Momentum-quality stock filter",
        "rank": "RESEARCH MORE / IMPLEMENTATION REJECTED NOW",
        "representative": None,
        "description": "One quality filter on the momentum universe; separate from composite",
        "confidence": "Unestablished; joined PIT fundamentals unavailable",
        "complexity": "Medium-high",
        "agentic_upside": "Timestamped hypotheses after a pure-momentum baseline",
    },
    {
        "candidate": "Momentum-quality composite score",
        "rank": "RESEARCH MORE / IMPLEMENTATION REJECTED NOW",
        "representative": None,
        "description": "Small rank composite, not tested or inferred from sleeve blending",
        "confidence": "Unestablished; extra complexity has no measured incremental support",
        "complexity": "High relative to simple baselines",
        "agentic_upside": "Challenge added-feature value; reject unearned complexity",
    },
    {
        "candidate": "Value sleeve",
        "rank": "WATCH",
        "representative": "long_value_drag0.005",
        "description": "Large high-book-to-market long portfolio, not a defensive hedge",
        "confidence": "Low-medium; regime dependence and unknown implementation",
        "complexity": "Medium",
        "agentic_upside": "Investigate value traps and changing accounting comparability",
    },
    {
        "candidate": "Joint quality/value",
        "rank": "REJECT full-sample winner; WATCH family",
        "representative": "joint_value_quality_drag0.005",
        "description": "Top-two value/profitability intersection baskets; not size controlled",
        "confidence": "Low; serious 2010s failure and missing holdings",
        "complexity": "Medium-high",
        "agentic_upside": "Explain lost decades rather than tune away the failure",
    },
    {
        "candidate": "Numeric PEAD / earnings momentum",
        "rank": "WATCH / IMPLEMENTATION REJECTED NOW",
        "representative": None,
        "description": "Earnings/revenue surprises, revisions, confirmation and guidance",
        "confidence": "No implementation evidence; free PIT consensus/timing missing",
        "complexity": "High",
        "agentic_upside": "Bounded guidance/text research after numeric validation",
    },
]


def main() -> None:
    metrics = pd.read_csv(RESULTS / "tournament.csv")
    cards = []
    for candidate in CANDIDATES:
        representative = candidate["representative"]
        if representative is None:
            measured = {
                "data_quality": "INSUFFICIENT",
                "backtest_quality": "NOT RUN; no substitute proxy",
                "cagr": None,
                "sharpe": None,
                "max_drawdown": None,
                "annual_traded_notional": None,
                "annual_transaction_cost_fraction": None,
                "worst_regime": None,
                "best_regime": None,
            }
        else:
            rows = metrics[metrics.name == representative]
            measured = rows[rows.period == "full"].iloc[0].to_dict()
            regimes = rows[
                rows.period.isin(["pre2000", "2000_2007", "2008_2009", "2010_2019", "2020_onward"])
            ]
            measured |= {
                "backtest_quality": "EXPLORATORY; see source/sample limitations",
                "worst_regime": regimes.loc[regimes.cagr.idxmin(), "period"],
                "best_regime": regimes.loc[regimes.cagr.idxmax(), "period"],
                "cost_type": "Measured simulated traded-notional fees"
                if measured["tradable_holdings_known"]
                else "Assumed annual internal drag, not observed turnover",
            }
        cards.append(
            {
                **candidate,
                **measured,
                "long_only_compatible": True,
                "robinhood_compatibility": (
                    "Conceptually long equity/ETF; entitlement, sizing and settlement unverified"
                ),
                "production_ready": False,
            }
        )
    pd.DataFrame(cards).to_csv(RESULTS / "candidate_summary.csv", index=False, float_format="%.8g")
    names = [candidate["representative"] for candidate in CANDIDATES if candidate["representative"]]
    metrics[metrics.name.isin(names)].to_csv(
        RESULTS / "candidate_regimes.csv", index=False, float_format="%.8g"
    )
    parameters = metrics[
        metrics.family.isin(["trend", "ETF trend", "stock momentum"])
        & metrics.scenario.isin(["5bps_rf", "15bps"])
    ].copy()
    # Separate actual ETF universes rather than blending unlike assets/sample windows.
    parameters["universe"] = parameters.name.str.extract(r"^(SPY_AGG|SPY|market|stocks)")[0]
    parameter_table = parameters.groupby(["universe", "period"]).agg(
        variants=("name", "count"),
        cagr_min=("cagr", "min"),
        cagr_median=("cagr", "median"),
        cagr_max=("cagr", "max"),
        sharpe_median=("sharpe", "median"),
        maxdd_min=("max_drawdown", "min"),
        maxdd_median=("max_drawdown", "median"),
        maxdd_max=("max_drawdown", "max"),
    )
    parameter_table.to_csv(RESULTS / "parameter_neighborhoods.csv", float_format="%.8g")
    curves = pd.read_csv(RESULTS / "monthly_returns.csv", index_col=0, parse_dates=True)
    sleeve_names = [
        "market_sma10_rf_5bps",
        "long_momentum_drag0.015",
        "long_quality_drag0.005",
        "long_value_drag0.005",
    ]
    correlations = {}
    for label, start, end in (
        ("1964_1999", "1964", "1999"),
        ("2000_2009", "2000", "2009"),
        ("2010_2019", "2010", "2019"),
        ("2020_onward", "2020", None),
    ):
        correlations[label] = curves.loc[start:end, sleeve_names].dropna().corr().to_dict()
    (RESULTS / "sleeve_correlations_by_regime.json").write_text(
        json.dumps(correlations, indent=2) + "\n"
    )
    print(json.dumps({"candidate_cards": len(cards), "numeric_gate_failures": 3}))


if __name__ == "__main__":
    main()

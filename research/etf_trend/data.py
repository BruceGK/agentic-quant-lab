"""Issuer NAV/distribution reconstruction and explicit execution-price data limitations."""

import argparse
import hashlib
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from research.data import CACHE as SHARED_CACHE
from research.data import ROOT as RESEARCH_ROOT
from research.data import fetch, french_returns
from research.engine import row_at
from research.etf_trend.experiment import END
from research.etf_trend.run import OUTPUT

CACHE = SHARED_CACHE / "etf_trend"
BASE = "https://www.ssga.com/library-content/products/"
URLS = {
    "SPY_nav.xlsx": BASE + "fund-data/etfs/us/navhist-us-en-spy.xlsx",
    "BIL_nav.xlsx": BASE + "fund-data/etfs/us/navhist-us-en-bil.xlsx",
    "distributions.xlsx": BASE + "fund-data/etfs/us/spdr-etf-historical-distributions.xlsx",
    "SPY_premium.xlsx": BASE + "fund-data/etfs/us/pdhist-us-en-spy.xlsx",
    "BIL_premium.xlsx": BASE + "fund-data/etfs/us/pdhist-us-en-bil.xlsx",
    "SPY_factsheet.pdf": BASE + "factsheets/etfs/us/factsheet-us-en-spy.pdf",
    "BIL_factsheet.pdf": BASE + "factsheets/etfs/us/factsheet-us-en-bil.pdf",
    "BIL_split.html": "https://www.splithistory.com/bil/",
    "SPY_page.html": "https://www.ssga.com/us/en/individual/etfs/spdr-sp-500-etf-trust-spy",
    "BIL_page.html": (
        "https://www.ssga.com/us/en/individual/etfs/"
        "state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil"
    ),
}
SPLIT_DATE = pd.Timestamp("2017-11-30")
# Issuer factsheets, June 30 2026, page 1: NAV total returns, percent.
CHECKPOINTS = {
    "SPY": {"qtd": 15.17, "ytd": 10.13, "1y": 22.15, "3y": 20.46, "5y": 13.26, "10y": 15.35},
    "BIL": {"qtd": 0.88, "ytd": 1.74, "1y": 3.83, "3y": 4.59, "5y": 3.46, "10y": 2.20},
}


def dated_table(data: pd.DataFrame, value_column: str) -> pd.DataFrame:
    dated = data.Date.astype(str).str.fullmatch(r"\d{2}-[A-Za-z]{3}-\d{4}")
    if pd.to_numeric(data.loc[~dated, value_column], errors="coerce").notna().any():
        raise ValueError("A numeric issuer observation has no valid date")
    data = data.loc[dated].copy()
    data["Date"] = pd.to_datetime(data["Date"], format="%d-%b-%Y", errors="raise")
    data = data.set_index("Date").sort_index()
    if data.index.has_duplicates:
        raise ValueError("Duplicate dated issuer observation")
    return data


def load_nav(path) -> pd.DataFrame:
    data = pd.read_excel(path, sheet_name="navhist", header=3)
    required = ["Date", "NAV", "Shares Outstanding", "Total Net Assets"]
    if list(data.columns[:4]) != required:
        raise ValueError("Issuer NAV schema changed")
    data = dated_table(data, "NAV")
    data["NAV"] = pd.to_numeric(data["NAV"], errors="raise")
    if data.index.has_duplicates or not np.isfinite(data.NAV).all() or (data.NAV <= 0).any():
        raise ValueError("Invalid or duplicate issuer NAV")
    return data


def load_distributions(path, symbol: str) -> pd.DataFrame:
    data = pd.read_excel(path, sheet_name="dividend")
    data.columns = [str(name).strip() for name in data.columns]
    data = data.loc[data.TICKER == symbol].copy()
    for name in ("EX-DATE", "PAYABLE DATE", "RECORD DATE"):
        data[name] = pd.to_datetime(data[name], format="%m/%d/%Y", errors="raise")
    columns = ("DIVIDEND ($)", "SHORT TERM CAPITAL GAIN ($)", "LONG TERM CAPITAL GAIN ($)")
    for column in columns:
        data[column] = pd.to_numeric(data[column].fillna(0), errors="raise")
    data["distribution"] = data[list(columns)].sum(axis=1)
    data = data.set_index("EX-DATE").sort_index()
    # A 2008 BIL payment-date error is outside this frozen 2014+ audit window.
    # Do not infer or repair that date, and do not use it in this reconstruction.
    data = data.loc["2014-01-01":END]
    if data.index.has_duplicates or (data.distribution < 0).any():
        raise ValueError("Unexpected duplicate or negative distribution")
    if (data["PAYABLE DATE"] < data.index).any():
        raise ValueError("Distribution payable before its ex-date")
    return data


def total_return(nav: pd.Series, distributions: pd.Series, split_ratio: pd.Series) -> pd.DataFrame:
    if not nav.index.equals(split_ratio.index) or not nav.index.equals(distributions.index):
        raise ValueError("Corporate actions and NAV must share the exact session calendar")
    if not np.isfinite(nav).all() or (nav <= 0).any() or (split_ratio <= 0).any():
        raise ValueError("Invalid NAV or split ratio")
    previous = nav.shift(1)
    price_return = split_ratio * nav / previous - 1
    income_return = split_ratio * distributions / previous
    returns = price_return + income_return
    returns.iloc[0] = 0
    income_return.iloc[0] = 0
    price_return.iloc[0] = 0
    return pd.DataFrame(
        {
            "raw_nav": nav,
            "distribution": distributions,
            "new_shares_per_old": split_ratio,
            "price_return": price_return,
            "distribution_return": income_return,
            "total_return": returns,
            "total_return_level": (1 + returns).cumprod() * 100,
        }
    )


def payable_total_return(
    nav: pd.Series, events: pd.DataFrame, split_ratio: pd.Series
) -> pd.DataFrame:
    if not nav.index.equals(split_ratio.index):
        raise ValueError("Share units and NAV must share the same calendar")
    nav_values = nav.to_numpy(dtype=float)
    ratios = split_ratio.to_numpy(dtype=float)
    if (
        not len(nav_values)
        or not np.isfinite(nav_values).all()
        or not np.isfinite(ratios).all()
        or np.any(nav_values <= 0)
        or np.any(ratios <= 0)
    ):
        raise ValueError("NAV and share-unit ratios must be positive and finite")
    units = 1.0
    receivables: dict[pd.Timestamp, float] = {}
    rows = []
    previous_wealth = float(nav_values[0])
    for i, day in enumerate(nav.index):
        if not isinstance(day, pd.Timestamp):
            raise ValueError("Issuer observations need dated sessions")
        price = float(nav_values[i])
        old_units = units
        if i:
            units *= float(ratios[i])
        distribution_income = 0.0
        # A new position at the initial close does not own that day's distribution.
        if i > 0 and day in events.index:
            event = row_at(events, day)
            payable = event["PAYABLE DATE"]
            if not isinstance(payable, pd.Timestamp) or payable < day:
                raise ValueError("Invalid distribution payment timestamp")
            distribution_income = units * float(event.distribution)
            receivables[payable] = receivables.get(payable, 0.0) + distribution_income
        paid = sum(amount for date, amount in receivables.items() if date <= day)
        receivables = {date: amount for date, amount in receivables.items() if date > day}
        units += paid / price
        unpaid = sum(receivables.values())
        wealth = units * price + unpaid
        gain = wealth / previous_wealth - 1 if i else 0.0
        price_gain = (
            (old_units * float(ratios[i]) * price - old_units * float(nav_values[i - 1]))
            / previous_wealth
            if i
            else 0.0
        )
        income_gain = distribution_income / previous_wealth
        if not np.isclose(price_gain + income_gain, gain, atol=1e-12):
            raise ArithmeticError("Issuer share/receivable total return did not reconcile")
        rows.append(
            {
                "Date": day,
                "raw_nav": price,
                "total_return": gain,
                "price_return": price_gain,
                "distribution_return": income_gain,
                "total_return_level": wealth / float(nav_values[0]) * 100,
                "reinvested_units": units,
                "unpaid_distribution_value": unpaid,
            }
        )
        previous_wealth = wealth
    return pd.DataFrame(rows).set_index("Date")


def checkpoints(nav: pd.Series, events: pd.DataFrame, splits: pd.Series, symbol: str) -> list[dict]:
    end = pd.Timestamp("2026-06-30")
    boundaries = {
        "qtd": pd.Timestamp("2026-03-31"),
        "ytd": pd.Timestamp("2025-12-31"),
        "1y": pd.Timestamp("2025-06-30"),
        "3y": pd.Timestamp("2023-06-30"),
        "5y": pd.Timestamp("2021-06-30"),
        "10y": pd.Timestamp("2016-06-30"),
    }
    rows = []
    for period, start in boundaries.items():
        years = {"3y": 3, "5y": 5, "10y": 10}.get(period, 1)
        window = payable_total_return(nav.loc[start:end], events, splits.loc[start:end])
        measured = (window.total_return_level.iloc[-1] / 100) ** (1 / years) - 1
        expected = CHECKPOINTS[symbol][period] / 100
        rows.append(
            {
                "symbol": symbol,
                "period": period,
                "end": str(end.date()),
                "reconstructed_return": float(measured),
                "issuer_nav_return": expected,
                "difference_bps": float((measured - expected) * 10000),
                "within_2bps": bool(abs(measured - expected) <= 0.0002),
            }
        )
    return rows


def prepare() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    previous_path = OUTPUT / "data_manifest.json"
    prior = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    hashes = {item["path"]: item["sha256"] for item in prior.get("sources", [])}
    sources = [
        fetch(url, CACHE / name, hashes.get(str((CACHE / name).relative_to(RESEARCH_ROOT))))
        for name, url in URLS.items()
    ]
    rf_path = SHARED_CACHE / "ff_daily.zip"
    sources.append(
        {
            "path": str(rf_path.relative_to(RESEARCH_ROOT)),
            "sha256": hashlib.sha256(rf_path.read_bytes()).hexdigest(),
            "bytes": rf_path.stat().st_size,
            "url": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip",
        }
    )
    riskfree = french_returns("ff_daily").RF.loc["2014-01-01":END]
    panels, audit_rows, performance = {}, [], []
    for symbol in ("SPY", "BIL"):
        full = load_nav(CACHE / f"{symbol}_nav.xlsx")
        nav = full.loc["2014-01-01":END].NAV
        extra = nav.index.difference(riskfree.index)
        if not nav.index.equals(riskfree.index):
            missing = riskfree.index.difference(nav.index)
            if len(missing):
                raise ValueError(f"Missing exchange-session NAV for {symbol}: {list(missing)}")
            # Issuer may publish a valuation on an exchange holiday (2014 Good Friday).
            # The independent US equity return calendar, not valuation dates, defines execution.
            nav = nav.reindex(riskfree.index)
        events = load_distributions(CACHE / "distributions.xlsx", symbol)
        selected_events = events.loc[nav.index[0] : END]
        if not selected_events.index.isin(nav.index).all():
            raise ValueError("An ex-distribution date lacks a NAV observation")
        dividends = selected_events.distribution.reindex(nav.index, fill_value=0)
        splits = pd.Series(1.0, index=nav.index)
        if symbol == "BIL":
            before, after = row_at(full, pd.Timestamp("2017-11-29")), row_at(full, SPLIT_DATE)
            if not np.isclose(
                float(after["Shares Outstanding"]) / float(before["Shares Outstanding"]), 0.5
            ) or not np.isclose(float(after.NAV) / float(before.NAV), 2, atol=0.001):
                raise ValueError(
                    "Issuer share-unit evidence no longer confirms the BIL reverse split"
                )
            if "November 30, 2017" not in (CACHE / "BIL_split.html").read_text():
                raise ValueError("Independent split-date confirmation is missing")
            splits.at[SPLIT_DATE] = 0.5
        ex_date = total_return(nav, dividends, splits)
        reconstructed = payable_total_return(nav, selected_events, splits)
        if reconstructed.total_return.abs().max() > (0.2 if symbol == "SPY" else 0.02):
            raise ValueError("Unexplained discontinuity remains after corporate-action adjustment")
        reconstructed.to_csv(CACHE / f"{symbol}_reconstructed.csv", float_format="%.14g")
        ex_date.to_csv(CACHE / f"{symbol}_exdate_reconstruction.csv", float_format="%.14g")
        panels[symbol] = reconstructed.total_return_level
        performance.extend(checkpoints(nav, selected_events, splits, symbol))
        premium = pd.read_excel(CACHE / f"{symbol}_premium.xlsx", sheet_name="pdhist", header=3)
        premium = dated_table(premium, "Premium/Discount")
        audit_rows.append(
            {
                "symbol": symbol,
                "source_type": "issuer NAV, not exchange closing transactions",
                "first_date": str(nav.index[0].date()),
                "last_date": str(nav.index[-1].date()),
                "sessions": len(nav),
                "matched_independent_rf_calendar": True,
                "excluded_nonexchange_valuation_dates": [str(day.date()) for day in extra],
                "distribution_events": len(selected_events),
                "explicit_zero_distributions": int(selected_events.distribution.eq(0).sum()),
                "max_payment_lag_days": int(
                    (selected_events["PAYABLE DATE"] - selected_events.index).dt.days.max()
                ),
                "max_abs_adjusted_daily_return": float(reconstructed.total_return.abs().max()),
                "maximum_unpaid_distribution_fraction": float(
                    (
                        reconstructed.unpaid_distribution_value
                        / (reconstructed.total_return_level / 100 * float(nav.iloc[0]))
                    ).max()
                ),
                "exdate_vs_paydate_reinvestment_endpoint_difference": float(
                    ex_date.total_return_level.iloc[-1] / reconstructed.total_return_level.iloc[-1]
                    - 1
                ),
                "premium_history_first": str(premium.index[0].date()),
                "premium_history_last": str(premium.index[-1].date()),
                "premium_rows": len(premium),
                "split_event": "2017-11-30 1 new for 2 old" if symbol == "BIL" else "none observed",
            }
        )
    checks = pd.DataFrame(performance)
    checks.to_csv(OUTPUT / "issuer_return_crosschecks.csv", index=False, float_format="%.12g")
    (OUTPUT / "data_audit.json").write_text(json.dumps(audit_rows, indent=2) + "\n")
    panel = pd.DataFrame({"SPY": panels["SPY"], "DEFENSIVE": panels["BIL"], "RF": riskfree})
    path = CACHE / "audited_panel.csv"
    panel.to_csv(path, float_format="%.14g")
    passed = bool(checks.within_2bps.all())
    manifest = {
        "retrieved_at": prior.get("retrieved_at", datetime.now(UTC).isoformat()),
        "audit_status": "EXPLORATORY_LIMITATIONS" if passed else "FAILED_CROSSCHECK",
        "classification": "EXPLORATORY_NAV_PROXY_NOT_EXECUTABLE_CLOSE",
        "sources": sources,
        "panel_path": str(path.relative_to(RESEARCH_ROOT)),
        "panel_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "corporate_actions": {"BIL": {"2017-11-30": 0.5}, "SPY": {}},
        "defensive_proxy_splicing": False,
        "limitations": [
            "Official NAV, not exchange closing transactions; next-session NAV is a proxy.",
            "Ex-date receivables reinvest at payment; total-return units are not tradable shares.",
            (
                "Switching whole total-return units ignores small unpaid-distribution constraints; "
                "this is not a broker simulation."
            ),
            "Revised issuer vintage; split source and issuer return checkpoints cross-checked.",
            "Fund expenses already in NAV; only external transaction costs are added.",
        ],
    }
    previous_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps({"audit": manifest["audit_status"], "rows": len(panel), "details": audit_rows})
    )
    print(checks.to_string(index=False))
    if not passed:
        raise ValueError("Reconstructed returns do not match the independent issuer checkpoints")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    prepare()

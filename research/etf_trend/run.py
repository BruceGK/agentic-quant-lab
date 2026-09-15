"""Execute the fixed ETF experiment on an audited local panel, never fetch data here."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.data import ROOT as RESEARCH_ROOT
from research.engine import date_index
from research.etf_trend.decompose import (
    attribution,
    defensive_spells,
    episode_events,
    equity_drawdowns,
)
from research.etf_trend.experiment import (
    COSTS,
    END,
    MODELS,
    START,
    metrics,
    reject_advanced_signals,
    run_fixed,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results"
REGIMES = {
    "2016_2019": ("2016-01-01", "2019-12-31"),
    "covid2020": ("2020-01-01", "2020-12-31"),
    "2021": ("2021-01-01", "2021-12-31"),
    "inflation2022": ("2022-01-01", "2022-12-31"),
    "2023_2025": ("2023-01-01", "2025-12-31"),
    "2026_YTD": ("2026-01-01", "2026-07-31"),
}


def load_audited_panel() -> tuple[pd.DataFrame, pd.Series, dict]:
    manifest = json.loads((OUTPUT / "data_manifest.json").read_text())
    if manifest["audit_status"] not in ("PASSED", "EXPLORATORY_LIMITATIONS"):
        raise ValueError("Unverified data cannot enter the ETF comparison")
    for source in manifest["sources"]:
        path = (RESEARCH_ROOT / source["path"]).resolve()
        if not path.is_relative_to((RESEARCH_ROOT / ".cache").resolve()):
            raise ValueError("Raw sources must stay inside the ignored research cache")
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Raw ETF data changed from the audited vintage")
    path = (RESEARCH_ROOT / manifest["panel_path"]).resolve()
    if not path.is_relative_to((RESEARCH_ROOT / ".cache").resolve()):
        raise ValueError("Audited panel must stay in ignored research cache")
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["panel_sha256"]:
        raise ValueError("Prepared ETF panel changed after data audit")
    panel = pd.read_csv(path, index_col=0, parse_dates=True)
    if list(panel.columns) != ["SPY", "DEFENSIVE", "RF"]:
        raise ValueError("Expected exactly two total-return levels and an independent RF return")
    panel = panel.loc[:END]
    if not np.isfinite(panel.to_numpy()).all() or panel.index.has_duplicates:
        raise ValueError("Audited panel must be complete and unique")
    if panel.index[0] > pd.Timestamp("2014-12-31") or panel.index[-1] != END:
        raise ValueError("Panel does not cover the predeclared warmup and endpoint")
    return panel[["SPY", "DEFENSIVE"]], panel.RF, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    p, rf, source_manifest = load_audited_panel()
    OUTPUT.mkdir(exist_ok=True)
    audit = reject_advanced_signals(p)
    (OUTPUT / "lookahead_falsification.json").write_text(json.dumps(audit, indent=2) + "\n")
    benchmark = run_fixed(p, "SPY", 0, "BIL").run.returns
    records, annual_rows, regimes, decisions = [], [], [], []
    spell_rows, event_rows, attribution_rows = [], [], []
    return_series: dict[str, pd.Series] = {}
    episodes = equity_drawdowns(p.SPY.loc[START:])
    (OUTPUT / "equity_drawdowns.json").write_text(json.dumps(episodes, indent=2) + "\n")
    for defense in ("BIL", "ZERO_CASH"):
        for cost in COSTS:
            for model in MODELS:
                result = run_fixed(p, model, cost, defense)
                name = f"{model}_{defense}_{cost}bps"
                record = metrics(result, rf, benchmark)
                record["classification"] = source_manifest["classification"]
                evaluation = result.run.returns.loc[START:]
                wealth = (1 + evaluation).cumprod()
                high = wealth.cummax().clip(lower=1.0)
                drawdown = wealth / high - 1
                trough_date = drawdown.idxmin()
                prefix = wealth.loc[:trough_date]
                peak_date = prefix.idxmax()
                record["max_drawdown_peak"] = str(peak_date)
                record["max_drawdown_trough"] = str(trough_date)
                records.append(record)
                selected = result.run.returns.loc[START:]
                return_series[name] = selected
                for year, values in selected.groupby(date_index(selected.index).year):
                    annual_rows.append(
                        {
                            "name": name,
                            "year": int(year),
                            "return": float(np.prod(1 + values.to_numpy()) - 1),
                            "complete_calendar_year": int(year) != 2026,
                        }
                    )
                for regime, (left, right) in REGIMES.items():
                    r = selected.loc[left:right]
                    if r.empty:
                        continue
                    years = len(r) / 252
                    wealth = np.r_[1.0, np.cumprod(1 + r.to_numpy())]
                    regimes.append(
                        {
                            "name": name,
                            "regime": regime,
                            "start": str(r.index[0].date()),
                            "end": str(r.index[-1].date()),
                            "cagr": float(wealth[-1] ** (1 / years) - 1),
                            "return": float(wealth[-1] - 1),
                            "max_drawdown": float(
                                (wealth / np.maximum.accumulate(wealth) - 1).min()
                            ),
                            "daily_arithmetic_mean_excess_vs_spy": float(
                                (r - benchmark.loc[r.index]).mean() * 252
                            ),
                        }
                    )
                if model in ("ABS12", "SMA10"):
                    log = result.decisions.copy()
                    log["model"], log["defense"], log["cost_bps"] = model, defense, cost
                    log["decision_date"] = log.index
                    decisions.extend(log.to_dict("records"))
                    spells = defensive_spells(result, p)
                    spell_rows.extend(spells)
                    event_rows.extend(episode_events(result, episodes, spells, p))
                    _, attr = attribution(result, p)
                    attribution_rows.append(attr)
    pd.DataFrame(records).to_csv(OUTPUT / "metrics.csv", index=False, float_format="%.10g")
    pd.DataFrame(annual_rows).to_csv(
        OUTPUT / "calendar_returns.csv", index=False, float_format="%.10g"
    )
    pd.DataFrame(regimes).to_csv(OUTPUT / "regimes.csv", index=False, float_format="%.10g")
    pd.DataFrame(decisions).to_csv(OUTPUT / "decisions.csv", index=False)
    pd.DataFrame(spell_rows).to_csv(
        OUTPUT / "defensive_spells.csv", index=False, float_format="%.10g"
    )
    spell_frame = pd.DataFrame(spell_rows)
    spell_summary = []
    for (model, defense, cost), group in spell_frame.groupby(["model", "defense", "cost_bps"]):
        ratios = np.log1p(group.net_relative_wealth_vs_staying_spy.to_numpy())
        whipsaw = group.whipsaw.to_numpy(dtype=bool)
        name = f"{model}_{defense}_{cost}bps"
        spy_name = f"SPY_{defense}_{cost}bps"
        total_relative = float(
            np.log1p(return_series[name]).sum() - np.log1p(return_series[spy_name]).sum()
        )
        residual = total_relative - float(ratios.sum())
        if abs(residual) > 1e-8:
            raise ArithmeticError(
                "Whole-sample timing loss does not equal nonoverlapping spell losses"
            )
        spell_summary.append(
            {
                "model": model,
                "defense": defense,
                "cost_bps": cost,
                "completed_defensive_spells": int((~group.open_right_censored).sum()),
                "whipsaw_spells": int(whipsaw.sum()),
                "short_whipsaw_spells": int(
                    (group.whipsaw & group.short_spell_at_most_3_calendar_months).sum()
                ),
                "defensive_sessions": int(group.defensive_sessions.sum()),
                "total_log_relative_wealth": total_relative,
                "whipsaw_log_relative_wealth": float(ratios[whipsaw].sum()),
                "other_spells_log_relative_wealth": float(ratios[~whipsaw].sum()),
                "relative_terminal_wealth_vs_spy": float(np.expm1(total_relative)),
                "spell_accounting_residual": residual,
            }
        )
    pd.DataFrame(spell_summary).to_csv(OUTPUT / "whipsaw_summary.csv", index=False)
    pd.DataFrame(event_rows).to_csv(
        OUTPUT / "drawdown_events.csv", index=False, float_format="%.10g"
    )
    pd.DataFrame(attribution_rows).to_csv(
        OUTPUT / "attribution.csv", index=False, float_format="%.10g"
    )
    returns = pd.DataFrame(return_series)
    returns.to_csv(OUTPUT / "daily_returns.csv", float_format="%.12g")
    agreement, concentration = [], []
    for cost in COSTS:
        absolute = run_fixed(p, "ABS12", cost, "BIL")
        average = run_fixed(p, "SMA10", cost, "BIL")
        a = absolute.run.weights.SPY.loc[START:].gt(0.5)
        b = average.run.weights.SPY.loc[START:].gt(0.5)
        agreement.append(
            {
                "cost_bps": cost,
                "state_agreement": float(a.eq(b).mean()),
                "both_defensive_sessions": int((~a & ~b).sum()),
                "abs_only_defensive_sessions": int((~a & b).sum()),
                "sma_only_defensive_sessions": int((a & ~b).sum()),
            }
        )
        for model in ("ABS12", "SMA10"):
            name = f"{model}_BIL_{cost}bps"
            excess_log = pd.Series(
                np.log1p(returns[name]) - np.log1p(returns[f"SPY_BIL_{cost}bps"]),
                index=returns.index,
            )
            for regime, (left, right) in REGIMES.items():
                selection = excess_log.loc[left:right]
                concentration.append(
                    {
                        "model": model,
                        "cost_bps": cost,
                        "regime": regime,
                        "log_wealth_excess_vs_same_cost_spy": float(selection.sum()),
                        "rest_of_sample_log_excess": float(excess_log.sum() - selection.sum()),
                        "attribution_not_a_restarted_tradable_path": True,
                    }
                )
    pd.DataFrame(agreement).to_csv(OUTPUT / "rule_agreement.csv", index=False)
    pd.DataFrame(concentration).to_csv(OUTPUT / "crisis_contributions.csv", index=False)
    metadata = {
        "protocol_sha256": hashlib.sha256((ROOT / "protocol.md").read_bytes()).hexdigest(),
        "source_manifest_sha256": hashlib.sha256(
            (OUTPUT / "data_manifest.json").read_bytes()
        ).hexdigest(),
        "code_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(ROOT.glob("*.py"))
        },
        "shared_engine_sha256": hashlib.sha256(
            (RESEARCH_ROOT / "engine.py").read_bytes()
        ).hexdigest(),
        "results_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(OUTPUT.glob("*.csv"))
        },
        "scenario_count": len(records),
        "fixed_rules_only": True,
        "lookahead_versions_rejected": audit,
    }
    (OUTPUT / "experiment_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps(
            {"fixed_scenarios": len(records), "major_drawdowns": len(episodes), "lookahead": audit}
        )
    )


if __name__ == "__main__":
    main()

"""Public-data acquisition and strict adapters; never accesses accounts or Phase 0 state."""

import argparse
import csv
import hashlib
import json
import re
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from research.engine import date_index

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".cache"
RESULTS = ROOT / "results"
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
QSTK = (
    "https://raw.githubusercontent.com/QuantSoftware/QuantSoftwareToolkit/"
    "0eb2c7a776c259a087fdcac1d3ff883eb0b5516c/QSTK/QSData/Yahoo/"
)
QSTRADER = (
    "https://raw.githubusercontent.com/quantstart/qstrader/"
    "e6d86a3ac3dc507b26e27b1f20c2949a69438ef7/data/"
)
FRENCH_FILES = {
    "ff_monthly": "F-F_Research_Data_Factors_CSV.zip",
    "ff_daily": "F-F_Research_Data_Factors_daily_CSV.zip",
    "momentum6": "6_Portfolios_ME_Prior_12_2_CSV.zip",
    "profitability6": "6_Portfolios_ME_OP_2x3_CSV.zip",
    "value6": "6_Portfolios_2x3_CSV.zip",
    "value_quality25": "25_Portfolios_BEME_OP_5x5_CSV.zip",
    "industry10": "10_Industry_Portfolios_CSV.zip",
}
SECTORS = {
    "technology": "AAPL MSFT IBM ORCL INTC CSCO QCOM TXN NVDA ADP",
    "healthcare": "GILD AMGN BIIB JNJ PFE MRK BMY ABT MDT UNH",
    "consumer": "WMT COST TGT HD LOW MCD SBUX NKE DIS AMZN",
    "staples": "KO PEP PG CL KMB",
    "energy": "XOM CVX COP SLB OXY",
    "industrials": "CAT DE MMM GE HON UTX BA UPS FDX UNP CSX EMR",
    "financials": "JPM BAC WFC C GS MS AXP USB PNC BK",
    "telecom": "VZ T CMCSA",
    "utilities": "DUK SO D AEP XEL",
}
STOCK_SECTORS = {ticker: sector for sector, names in SECTORS.items() for ticker in names.split()}


def fetch(url: str, path: Path, expected_hash: str | None = None) -> dict:
    if path.exists():
        raw = path.read_bytes()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(
            Request(url, headers={"User-Agent": "AQL-offline-research/0.1"}), timeout=45
        ) as r:
            raw = r.read(25_000_001)
        if len(raw) > 25_000_000 or not raw:
            raise ValueError("Unexpected dataset size; do not accept truncated downloads")
        path.write_bytes(raw)
    checksum = hashlib.sha256(raw).hexdigest()
    if expected_hash is not None and checksum != expected_hash:
        raise ValueError(
            f"Source revision detected for {path.name}; preserve the original manifest"
        )
    return {"url": url, "path": str(path.relative_to(ROOT)), "sha256": checksum, "bytes": len(raw)}


def french_blocks(path: Path, weighting: str = "value") -> list[tuple[str, pd.DataFrame]]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError("Expected one French CSV per archive")
        raw = archive.read(names[0]).decode("utf-8-sig")
    lines = raw.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if not re.match(r"^\s*,", lines[i]):
            i += 1
            continue
        label = next((line.strip() for line in reversed(lines[:i]) if line.strip()), "returns")
        token = "Value Weight" if weighting == "value" else "Equal Weight"
        if not path.stem.startswith("ff_") and token.lower() not in label.lower():
            i += 1
            continue
        header = next(csv.reader([lines[i]]))
        j = i + 1
        rows = []
        while j < len(lines) and re.match(r"^\s*\d{6}(?:\d{2})?\s*,", lines[j]):
            rows.append(next(csv.reader([lines[j]])))
            j += 1
        if rows:
            if any(len(row) != len(header) for row in rows):
                raise ValueError("Malformed French return table")
            keys = [row[0].strip() for row in rows]
            fmt = "%Y%m%d" if len(keys[0]) == 8 else "%Y%m"
            index = pd.to_datetime(keys, format=fmt)
            if fmt == "%Y%m":
                index = index + pd.offsets.MonthEnd(0)
            frame = pd.DataFrame(
                [[float(value) for value in row[1:]] for row in rows],
                index=index,
                columns=[name.strip() for name in header[1:]],
            )
            frame = frame.mask(frame.isin([-99.99, -999.0]))
            if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
                raise ValueError("Unordered or duplicate French dates")
            blocks.append((label, frame))
        i = max(j, i + 1)
    if not blocks:
        raise ValueError(f"No dated returns in {path.name}")
    return blocks


def french_returns(key: str, weighting: str = "value") -> pd.DataFrame:
    blocks = french_blocks(CACHE / f"{key}.zip", weighting)
    if key.startswith("ff_"):
        frame = blocks[0][1]
    else:
        token = "Value Weight" if weighting == "value" else "Equal Weight"
        matches = [frame for label, frame in blocks if token.lower() in label.lower()]
        if not matches:
            raise ValueError(f"No {weighting}-weighted return block in {key}")
        frame = matches[0]
    frame = frame / 100.0
    if (frame < -1).any().any():
        raise ValueError("Invalid simple return")
    return frame.loc[:"2026-07-31"]


def read_prices(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    data.columns = [str(column).strip().lower().replace(" ", "_") for column in data.columns]
    required = {"date", "close", "adj_close", "volume"}
    if not required <= set(data.columns):
        raise ValueError("Adjusted closes and volume are required; price-only data is not accepted")
    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d")
    data = data.set_index("date").sort_index()
    if data.index.has_duplicates:
        raise ValueError("Duplicate price date")
    for column in ("close", "adj_close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    if not np.isfinite(data[list(required - {"date"})].to_numpy()).all():
        raise ValueError("Nonfinite price observations")
    if (data[["close", "adj_close"]] <= 0).any().any() or (data["volume"] < 0).any():
        raise ValueError("Invalid price/volume")
    return data


def price_panel(kind: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = sorted((CACHE / kind).glob("*.csv"))
    if not files:
        raise ValueError(f"Acquire {kind} first")
    frames = {path.stem: read_prices(path) for path in files}
    prices = pd.DataFrame({key: value["adj_close"] for key, value in frames.items()})
    raw = pd.DataFrame({key: value["close"] for key, value in frames.items()})
    volume = pd.DataFrame({key: value["volume"] for key, value in frames.items()})
    return prices, raw, volume


def acquire() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    manifest_path = RESULTS / "data_manifest.json"
    original = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    prior = {item["path"]: item["sha256"] for item in original.get("sources", [])}
    sources, unavailable = [], []
    for key, filename in FRENCH_FILES.items():
        path = CACHE / f"{key}.zip"
        sources.append(fetch(FRENCH + filename, path, prior.get(str(path.relative_to(ROOT)))))
    for symbol in ("SPY", "AGG"):
        path = CACHE / "etfs" / f"{symbol}.csv"
        sources.append(
            fetch(QSTRADER + f"{symbol}.csv", path, prior.get(str(path.relative_to(ROOT))))
        )
    for symbol in STOCK_SECTORS:
        path = CACHE / "stocks" / f"{symbol}.csv"
        try:
            sources.append(
                fetch(QSTK + f"{symbol}.csv", path, prior.get(str(path.relative_to(ROOT))))
            )
        except HTTPError as error:
            if error.code != 404:
                raise
            unavailable.append({"symbol": symbol, "reason": "absent from the pinned snapshot"})
        time.sleep(0.03)
    manifest = {
        "retrieved_at": original.get("retrieved_at", datetime.now(UTC).isoformat()),
        "classification": "EXPLORATORY",
        "sources": sources,
        "unavailable": unavailable,
        "price_bias": "Surviving fixed stock convenience panel; not historical index membership.",
        "french_bias": (
            "Revised academic baskets; constituents/internal trades/PIT vintages unavailable."
        ),
        "no_source_credentials": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    audit = []
    for source in sources:
        path = ROOT / source["path"]
        if path.suffix == ".zip":
            blocks = french_blocks(path)
            frame = blocks[0][1]
            audit.append(
                {
                    "dataset": path.stem,
                    "start": str(date_index(frame.index)[0].date()),
                    "end": str(date_index(frame.index)[-1].date()),
                    "rows": len(frame),
                    "columns": list(frame.columns),
                    "blocks": [label for label, _ in blocks],
                    "missing_cells": int(frame.isna().sum().sum()),
                }
            )
        else:
            frame = read_prices(path)
            audit.append(
                {
                    "dataset": path.parent.name + "/" + path.stem,
                    "start": str(date_index(frame.index)[0].date()),
                    "end": str(date_index(frame.index)[-1].date()),
                    "rows": len(frame),
                    "missing_cells": int(frame.isna().sum().sum()),
                    "adjustment_ratio_min": float((frame.adj_close / frame.close).min()),
                    "largest_abs_return": float(frame.adj_close.pct_change().abs().max()),
                }
            )
    (RESULTS / "data_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"downloaded_or_verified": len(sources), "unavailable": unavailable}))
    print(json.dumps(audit[:9], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("acquire",))
    parser.parse_args()
    acquire()

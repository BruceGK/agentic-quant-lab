from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np
import pandas as pd

from research.engine import Plan, plan_frame


class Strategy(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def hypothesis(self) -> str: ...

    @property
    def required_data(self) -> tuple[str, ...]: ...

    @property
    def metadata(self) -> dict[str, str | int | float]: ...

    def generate_signal(self, prices: pd.DataFrame) -> pd.DataFrame: ...

    def build_target(self, prices: pd.DataFrame) -> Plan: ...


@dataclass(frozen=True)
class FixtureStrategy:
    id: str
    name: str
    hypothesis: str
    kind: Literal["momentum", "trend", "weak", "null"]
    lookback: int = 3
    allocation: float = 0.2

    @property
    def required_data(self) -> tuple[str, ...]:
        return ("dated synthetic valuation indices",)

    @property
    def metadata(self) -> dict[str, str | int | float]:
        return {
            "id": self.id,
            "kind": self.kind,
            "lookback": self.lookback,
            "allocation": self.allocation,
            "mode": "demo",
        }

    def generate_signal(self, prices: pd.DataFrame) -> pd.DataFrame:
        if self.lookback < 2 or not 0 < self.allocation <= 1:
            raise ValueError("Invalid strategy lookback or allocation")
        if self.kind == "momentum":
            scores = prices.shift(1) / prices.shift(self.lookback + 1) - 1
        elif self.kind == "trend":
            scores = prices / prices.rolling(self.lookback).mean() - 1
        else:
            scores = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
            scores["DEMO_WEAK" if self.kind == "weak" else "DEMO_NULL"] = 1.0
        scores.iloc[: self.lookback + 1] = np.nan
        return scores

    def build_target(self, prices: pd.DataFrame) -> Plan:
        scores = self.generate_signal(prices)
        weights = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
        for date, row in scores.iterrows():
            if row.isna().all():
                continue
            weights.loc[date] = 0.0
            positive = row[row > 0].sort_values(ascending=False, kind="mergesort")
            if not positive.empty:
                chosen = positive.index if self.kind == "trend" else positive.index[:1]
                weights.loc[date, chosen] = self.allocation / len(chosen)
        return plan_frame(prices, weights)

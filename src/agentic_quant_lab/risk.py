import math
from dataclasses import dataclass, field
from datetime import datetime

from agentic_quant_lab.constitution import constitution


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    quantity: int
    reference_price: float
    decision_at: datetime
    strategy_id: str
    side: str = "BUY"
    instrument_type: str = "synthetic_etf"
    mode: str = "dry_run"

    @property
    def notional(self) -> float:
        return self.quantity * self.reference_price


@dataclass(frozen=True)
class PortfolioSnapshot:
    equity: float = 10_000
    cash: float = 10_000
    position_notionals: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskPolicy:
    allowed_symbols: tuple[str, ...] = ("DEMO_UP", "DEMO_WEAK", "DEMO_NULL")
    allowed_instrument_types: tuple[str, ...] = ("synthetic_etf",)
    max_position_notional: float = 2_500
    max_order_notional: float = 2_000
    max_concentration: float = 0.25
    max_decision_age_seconds: float = 172_800
    live_execution_enabled: bool = False

    def __post_init__(self) -> None:
        limits = (
            self.max_position_notional,
            self.max_order_notional,
            self.max_concentration,
            self.max_decision_age_seconds,
        )
        if not all(math.isfinite(value) and value > 0 for value in limits):
            raise ValueError("Risk limits must be finite and positive")
        if self.max_concentration > 1:
            raise ValueError("Concentration cannot exceed equity")


@dataclass(frozen=True)
class RiskDecision:
    checks: dict[str, bool]

    @property
    def approved(self) -> bool:
        return all(self.checks.values())


class RiskGate:
    """Demo BUY-only gate against a supplied snapshot; never a live authorization."""

    def __init__(self, policy: RiskPolicy | None = None):
        self.policy = policy or RiskPolicy()

    def evaluate(
        self, intent: OrderIntent, portfolio: PortfolioSnapshot, *, now: datetime
    ) -> RiskDecision:
        policy = self.policy
        finite = (
            math.isfinite(intent.reference_price)
            and intent.reference_price > 0
            and type(intent.quantity) is int
            and intent.quantity > 0
        )
        account_valid = (
            math.isfinite(portfolio.equity)
            and math.isfinite(portfolio.cash)
            and portfolio.equity > 0
            and 0 <= portfolio.cash <= portfolio.equity
            and all(
                math.isfinite(value) and value >= 0
                for value in portfolio.position_notionals.values()
            )
        )
        notional = intent.notional if finite else math.inf
        existing = portfolio.position_notionals.get(intent.symbol, 0)
        positions = sum(portfolio.position_notionals.values())
        account_valid = account_valid and math.isclose(
            portfolio.cash + positions, portfolio.equity, rel_tol=1e-9, abs_tol=0.01
        )
        age = (
            (now - intent.decision_at).total_seconds()
            if now.utcoffset() is not None and intent.decision_at.utcoffset() is not None
            else math.inf
        )
        return RiskDecision(
            {
                "live execution disabled": (
                    not policy.live_execution_enabled
                    and constitution()["live_execution"]["enabled"] is False
                ),
                "dry_run mode": intent.mode == "dry_run",
                "allowed symbol": intent.symbol in policy.allowed_symbols,
                "allowed instrument": intent.instrument_type in policy.allowed_instrument_types,
                "positive whole-share long-only BUY": finite and intent.side == "BUY",
                "valid portfolio snapshot": account_valid,
                "no leverage": (
                    account_valid
                    and notional <= portfolio.cash
                    and positions + notional <= portfolio.equity
                ),
                "maximum order notional": notional <= policy.max_order_notional,
                "maximum position notional": (
                    account_valid and existing + notional <= policy.max_position_notional
                ),
                "maximum concentration": (
                    account_valid
                    and existing + notional <= portfolio.equity * policy.max_concentration
                    and all(
                        value <= portfolio.equity * policy.max_concentration
                        for value in portfolio.position_notionals.values()
                    )
                ),
                "fresh strategy decision": 0 <= age <= policy.max_decision_age_seconds,
            }
        )

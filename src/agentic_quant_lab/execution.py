from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol

from agentic_quant_lab.ledger import digest
from agentic_quant_lab.risk import OrderIntent, PortfolioSnapshot, RiskGate


class DisabledExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionReceipt:
    status: str
    mode: str
    data: str
    live_trading: str
    intent_hash: str
    symbol: str
    quantity: int
    estimated_notional: float
    message: str


class ExecutionAdapter(Protocol):
    def submit(self, intent: OrderIntent) -> ExecutionReceipt: ...


class DryRunExecutionAdapter:
    def __init__(self, gate: RiskGate, portfolio: PortfolioSnapshot, *, now: datetime):
        self.gate = gate
        self.portfolio = portfolio
        self.now = now

    def submit(self, intent: OrderIntent) -> ExecutionReceipt:
        decision = self.gate.evaluate(intent, self.portfolio, now=self.now)
        if not decision.approved:
            failed = ", ".join(name for name, passed in decision.checks.items() if not passed)
            raise DisabledExecutionError(f"Intent rejected: {failed}")
        payload = {**asdict(intent), "decision_at": intent.decision_at.isoformat()}
        return ExecutionReceipt(
            status="SIMULATED / DRY RUN",
            mode="demo",
            data="SYNTHETIC / FIXTURE",
            live_trading="DISABLED",
            intent_hash=digest(payload),
            symbol=intent.symbol,
            quantity=intent.quantity,
            estimated_notional=round(intent.notional, 2),
            message="Would submit only. Execution blocked because live execution is disabled.",
        )


class RobinhoodExecutionAdapter:
    def submit(self, intent: OrderIntent) -> ExecutionReceipt:
        raise DisabledExecutionError("Robinhood is not connected; live execution is disabled")

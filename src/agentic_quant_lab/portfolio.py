import math
from dataclasses import dataclass
from datetime import datetime

from agentic_quant_lab.risk import OrderIntent, PortfolioSnapshot
from agentic_quant_lab.tournament import StrategyCandidate


@dataclass(frozen=True)
class PortfolioProposal:
    strategy_id: str
    weights: dict[str, float]
    cash_weight: float
    intent: OrderIntent


def propose_portfolio(
    candidate: StrategyCandidate,
    targets: dict[str, float],
    prices: dict[str, float],
    snapshot: PortfolioSnapshot,
    decision_at: datetime,
) -> PortfolioProposal:
    if candidate.source != "demo" or candidate.status != "SURVIVES (DEMO ONLY)":
        raise ValueError("Only a surviving demo candidate can enter the demo portfolio")
    if (
        not targets
        or not all(math.isfinite(w) and 0 <= w <= 1 for w in targets.values())
        or sum(targets.values()) > 1
    ):
        raise ValueError("Invalid long-only target weights")
    selected = {symbol: weight for symbol, weight in targets.items() if weight > 0}
    if len(selected) != 1 or snapshot.position_notionals:
        raise ValueError("Demo allocator supports one sleeve and an initially all-cash account")
    symbol, weight = next(iter(selected.items()))
    price = prices[symbol]
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Invalid reference price")
    quantity = math.floor(snapshot.equity * weight / price)
    if quantity <= 0:
        raise ValueError("Insufficient capital for a whole share")
    return PortfolioProposal(
        strategy_id=candidate.id,
        weights=selected,
        cash_weight=1 - sum(selected.values()),
        intent=OrderIntent(
            symbol=symbol,
            quantity=quantity,
            reference_price=price,
            decision_at=decision_at,
            strategy_id=candidate.id,
        ),
    )

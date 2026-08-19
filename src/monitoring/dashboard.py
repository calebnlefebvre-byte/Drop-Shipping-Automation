from dataclasses import dataclass, field

from ..economics.calculator import estimate_economics
from ..providers.base import ProductCandidate
from .ledger import LedgerRow


@dataclass
class PeriodResult:
    name: str
    channel: str
    units_sold: int
    revenue: float
    net_profit: float
    net_margin_pct: float
    alerts: list[str] = field(default_factory=list)


def compute_period_result(row: LedgerRow) -> PeriodResult:
    """Turns one ledger row into a per-SKU profit result, reusing the same
    fee-aware economics as product research and pricing so a SKU's real
    profitability is computed identically everywhere in this project.
    """
    per_unit_ad_cost = (row.ad_spend / row.units_sold) if row.units_sold else 0.0
    candidate = ProductCandidate(
        name=row.name,
        category=row.category,
        supplier_cost=row.supplier_cost,
        target_sell_price=row.sell_price,
        weight_lb=row.weight_lb,
        est_ad_cost_per_sale=per_unit_ad_cost,
    )
    economics = estimate_economics(candidate, row.channel)

    revenue = row.units_sold * row.sell_price
    net_profit = economics.net_profit * row.units_sold - row.refunds
    net_margin_pct = (net_profit / revenue * 100) if revenue else 0.0

    return PeriodResult(
        name=row.name,
        channel=row.channel,
        units_sold=row.units_sold,
        revenue=round(revenue, 2),
        net_profit=round(net_profit, 2),
        net_margin_pct=round(net_margin_pct, 1),
        alerts=_evaluate_alerts(row, net_profit, net_margin_pct),
    )


def _evaluate_alerts(row: LedgerRow, net_profit: float, net_margin_pct: float) -> list[str]:
    """Only real problems get surfaced -- a SKU with no triggered alert
    here shows up in the summary but never in the "needs attention"
    section, same "don't alert on every poll, only on a real transition"
    discipline as a health-check monitor.
    """
    alerts = []

    if net_profit < 0:
        alerts.append(f"UNPROFITABLE: net loss of ${-net_profit:.2f} this period")

    if row.min_net_margin_pct is not None and net_margin_pct < row.min_net_margin_pct:
        alerts.append(
            f"MARGIN BELOW TARGET: {net_margin_pct:.1f}% vs {row.min_net_margin_pct:.1f}% minimum"
        )

    if (
        row.inventory_on_hand is not None
        and row.reorder_threshold is not None
        and row.inventory_on_hand <= row.reorder_threshold
    ):
        alerts.append(
            f"STOCKOUT RISK: {row.inventory_on_hand} units on hand, "
            f"at/below reorder threshold of {row.reorder_threshold}"
        )

    return alerts

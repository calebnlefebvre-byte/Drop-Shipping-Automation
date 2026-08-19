import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..util import float_or_none, int_or_none


@dataclass
class LedgerRow:
    date: str
    name: str
    category: str
    channel: str
    units_sold: int
    supplier_cost: float
    sell_price: float
    ad_spend: float = 0.0
    refunds: float = 0.0
    weight_lb: Optional[float] = None
    inventory_on_hand: Optional[int] = None
    reorder_threshold: Optional[int] = None
    min_net_margin_pct: Optional[float] = None


def read_ledger(path: str) -> list[LedgerRow]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            LedgerRow(
                date=row["date"],
                name=row["name"],
                category=row["category"],
                channel=row["channel"],
                units_sold=int(row["units_sold"]),
                supplier_cost=float(row["supplier_cost"]),
                sell_price=float(row["sell_price"]),
                ad_spend=float(row.get("ad_spend") or 0.0),
                refunds=float(row.get("refunds") or 0.0),
                weight_lb=float_or_none(row.get("weight_lb")),
                inventory_on_hand=int_or_none(row.get("inventory_on_hand")),
                reorder_threshold=int_or_none(row.get("reorder_threshold")),
                min_net_margin_pct=float_or_none(row.get("min_net_margin_pct")),
            )
            for row in reader
        ]

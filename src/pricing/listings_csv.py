import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..util import float_or_none


@dataclass
class Listing:
    name: str
    category: str
    channel: str
    supplier_cost: float
    current_price: float
    min_net_margin_pct: float
    weight_lb: Optional[float] = None
    est_ad_cost_per_sale: Optional[float] = None
    competitor_low: Optional[float] = None
    floor_override: Optional[float] = None
    ceiling: Optional[float] = None


def read_listings(path: str) -> list[Listing]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            Listing(
                name=row["name"],
                category=row["category"],
                channel=row["channel"],
                supplier_cost=float(row["supplier_cost"]),
                current_price=float(row["current_price"]),
                min_net_margin_pct=float(row["min_net_margin_pct"]),
                weight_lb=float_or_none(row.get("weight_lb")),
                est_ad_cost_per_sale=float_or_none(row.get("est_ad_cost_per_sale")),
                competitor_low=float_or_none(row.get("competitor_low")),
                floor_override=float_or_none(row.get("floor")),
                ceiling=float_or_none(row.get("ceiling")),
            )
            for row in reader
        ]

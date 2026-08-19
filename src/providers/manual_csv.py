import csv
from pathlib import Path
from typing import Optional

from .base import ProductCandidate, ProductDataProvider


class ManualCsvProvider(ProductDataProvider):
    """Reads candidates from a CSV you fill in by hand.

    The default provider: no API key, no rate limit, no vendor lock-in.
    Good enough to start scoring real candidates today; swap in Keepa or
    Jungle Scout later without changing anything else.
    """

    def __init__(self, path: str):
        self.path = Path(path)

    def fetch_candidates(self) -> list[ProductCandidate]:
        with self.path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [
                ProductCandidate(
                    name=row["name"],
                    category=row["category"],
                    supplier_cost=float(row["supplier_cost"]),
                    target_sell_price=float(row["target_sell_price"]),
                    est_monthly_searches=_int_or_none(row.get("est_monthly_searches")),
                    competitor_count=_int_or_none(row.get("competitor_count")),
                    avg_competitor_rating=_float_or_none(row.get("avg_competitor_rating")),
                    weight_lb=_float_or_none(row.get("weight_lb")),
                    est_ad_cost_per_sale=_float_or_none(row.get("est_ad_cost_per_sale")),
                    notes=row.get("notes", ""),
                )
                for row in reader
            ]


def _int_or_none(value: Optional[str]) -> Optional[int]:
    return int(value) if value else None


def _float_or_none(value: Optional[str]) -> Optional[float]:
    return float(value) if value else None

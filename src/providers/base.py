from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductCandidate:
    name: str
    category: str
    supplier_cost: float
    target_sell_price: float
    est_monthly_searches: Optional[int] = None
    competitor_count: Optional[int] = None
    avg_competitor_rating: Optional[float] = None
    notes: str = ""

    @property
    def gross_margin(self) -> float:
        if self.target_sell_price <= 0:
            return 0.0
        return (self.target_sell_price - self.supplier_cost) / self.target_sell_price


class ProductDataProvider(ABC):
    """A source of product candidates plus whatever market signal it can attach.

    Swap the provider, not the pipeline -- the scorer and CLI never know
    which one is behind this interface. Real providers (Keepa, Jungle
    Scout) implement this same method and slot in without touching
    anything downstream.
    """

    @abstractmethod
    def fetch_candidates(self) -> list[ProductCandidate]:
        ...

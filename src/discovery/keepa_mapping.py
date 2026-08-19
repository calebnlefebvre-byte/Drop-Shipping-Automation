from dataclasses import dataclass
from typing import Optional

# Keepa's CSV type indices, as used in the "stats.current" convenience
# array on a product object. Per Keepa's documented CSV type table --
# verify against https://keepa.com/#!discuss/t/api-overview/ before
# trusting these on a real account; this sandbox has never made a live
# call to confirm them against an actual response.
CSV_AMAZON = 0  # Amazon's own price, cents
CSV_NEW = 1  # lowest third-party new price, cents
CSV_SALES_RANK = 3  # lower is better/more sales -- a demand proxy, not search volume
CSV_COUNT_NEW = 11  # number of active new offers -- a competitor-count proxy
CSV_RATING = 16  # star rating * 10 (e.g. 45 == 4.5 stars)
CSV_COUNT_REVIEWS = 17

_MISSING = (-1, None)


@dataclass
class KeepaSignal:
    asin: str
    name: str
    category: str
    current_price: Optional[float]
    sales_rank: Optional[int]
    new_offer_count: Optional[int]
    rating: Optional[float]
    review_count: Optional[int]


def _at(current: list, index: int):
    if not current or index >= len(current):
        return None
    return current[index]


def _cents_to_dollars(value) -> Optional[float]:
    if value in _MISSING:
        return None
    return round(value / 100, 2)


def _clean_int(value) -> Optional[int]:
    return None if value in _MISSING else value


def parse_product(raw: dict) -> KeepaSignal:
    """Maps one raw Keepa product object into a KeepaSignal.

    Deliberately doesn't guess at anything Keepa doesn't report: a
    missing field becomes None, never a default value, so it can't
    silently poison a downstream margin calculation.
    """
    current = (raw.get("stats") or {}).get("current") or []

    price = _cents_to_dollars(_at(current, CSV_AMAZON))
    if price is None:
        price = _cents_to_dollars(_at(current, CSV_NEW))

    raw_rating = _at(current, CSV_RATING)
    rating = None if raw_rating in _MISSING else round(raw_rating / 10, 1)

    category_tree = raw.get("categoryTree") or []
    category = category_tree[0]["name"] if category_tree else "Unknown"

    return KeepaSignal(
        asin=raw.get("asin", ""),
        name=raw.get("title", ""),
        category=category,
        current_price=price,
        sales_rank=_clean_int(_at(current, CSV_SALES_RANK)),
        new_offer_count=_clean_int(_at(current, CSV_COUNT_NEW)),
        rating=rating,
        review_count=_clean_int(_at(current, CSV_COUNT_REVIEWS)),
    )

import csv

from .keepa_mapping import KeepaSignal

FIELDNAMES = [
    "name",
    "category",
    "supplier_cost",
    "target_sell_price",
    "est_monthly_searches",
    "competitor_count",
    "avg_competitor_rating",
    "weight_lb",
    "est_ad_cost_per_sale",
    "notes",
]


def write_candidate_csv(signals: list[KeepaSignal], path: str) -> None:
    """Writes discovered signals in the exact CSV shape ManualCsvProvider
    expects, so the existing research pipeline (src/cli.py) runs
    unchanged against Keepa-discovered candidates.

    supplier_cost and est_ad_cost_per_sale are left blank on purpose --
    Keepa has no visibility into what you pay a supplier or spend on
    ads, and guessing either would poison every downstream margin
    calculation. est_monthly_searches is also left blank: Keepa's sales
    rank is a demand proxy, not a search volume, and writing it into
    that column would misrepresent the signal to the scorer -- it goes
    into `notes` instead, labeled for what it actually is.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for s in signals:
            notes = f"ASIN {s.asin}"
            if s.sales_rank is not None:
                notes += f"; Amazon sales rank {s.sales_rank}"
            if s.review_count is not None:
                notes += f"; {s.review_count} reviews"
            writer.writerow(
                {
                    "name": s.name,
                    "category": s.category,
                    "supplier_cost": "",
                    "target_sell_price": s.current_price,
                    "est_monthly_searches": "",
                    "competitor_count": s.new_offer_count if s.new_offer_count is not None else "",
                    "avg_competitor_rating": s.rating if s.rating is not None else "",
                    "weight_lb": "",
                    "est_ad_cost_per_sale": "",
                    "notes": notes,
                }
            )

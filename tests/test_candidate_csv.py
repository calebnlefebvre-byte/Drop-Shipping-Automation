import csv

from src.discovery.candidate_csv import write_candidate_csv
from src.discovery.keepa_mapping import KeepaSignal
from src.providers.manual_csv import ManualCsvProvider


def test_writes_expected_shape(tmp_path):
    signals = [
        KeepaSignal(
            asin="B001",
            name="Discovered Widget",
            category="Kitchen",
            current_price=19.99,
            sales_rank=12000,
            new_offer_count=6,
            rating=4.3,
            review_count=210,
        )
    ]
    out_path = tmp_path / "discovered.csv"
    write_candidate_csv(signals, str(out_path))

    rows = list(csv.DictReader(out_path.open()))
    assert rows[0]["name"] == "Discovered Widget"
    assert rows[0]["supplier_cost"] == ""
    assert rows[0]["est_monthly_searches"] == ""
    assert rows[0]["target_sell_price"] == "19.99"
    assert rows[0]["competitor_count"] == "6"
    assert rows[0]["avg_competitor_rating"] == "4.3"
    assert "ASIN B001" in rows[0]["notes"]
    assert "Amazon sales rank 12000" in rows[0]["notes"]


def test_output_feeds_directly_into_manual_csv_provider_once_cost_is_filled_in(tmp_path):
    """Proves the design goal: a discovered CSV, with supplier_cost hand-filled,
    is directly readable by the existing research pipeline -- no separate code path.
    """
    signals = [
        KeepaSignal(
            asin="B002",
            name="Fillable Widget",
            category="Home",
            current_price=15.99,
            sales_rank=5000,
            new_offer_count=3,
            rating=4.0,
            review_count=80,
        )
    ]
    out_path = tmp_path / "discovered.csv"
    write_candidate_csv(signals, str(out_path))

    rows = list(csv.DictReader(out_path.open()))
    rows[0]["supplier_cost"] = "4.50"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    candidates = ManualCsvProvider(str(out_path)).fetch_candidates()
    assert len(candidates) == 1
    assert candidates[0].supplier_cost == 4.50
    assert candidates[0].target_sell_price == 15.99
    assert candidates[0].name == "Fillable Widget"

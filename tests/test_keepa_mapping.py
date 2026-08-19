from src.discovery.keepa_mapping import (
    CSV_AMAZON,
    CSV_COUNT_NEW,
    CSV_COUNT_REVIEWS,
    CSV_NEW,
    CSV_RATING,
    CSV_SALES_RANK,
    parse_product,
)


def make_current(overrides=None):
    current = [-1] * 20
    defaults = {
        CSV_AMAZON: 1999,
        CSV_NEW: 2099,
        CSV_SALES_RANK: 15000,
        CSV_COUNT_NEW: 8,
        CSV_RATING: 45,
        CSV_COUNT_REVIEWS: 320,
    }
    current_map = {**defaults, **(overrides or {})}
    for idx, val in current_map.items():
        current[idx] = val
    return current


def test_parses_full_product():
    raw = {
        "asin": "B00TEST123",
        "title": "Test Widget",
        "categoryTree": [{"name": "Kitchen"}, {"name": "Kitchen & Dining"}],
        "stats": {"current": make_current()},
    }
    signal = parse_product(raw)
    assert signal.asin == "B00TEST123"
    assert signal.name == "Test Widget"
    assert signal.category == "Kitchen"
    assert signal.current_price == 19.99
    assert signal.sales_rank == 15000
    assert signal.new_offer_count == 8
    assert signal.rating == 4.5
    assert signal.review_count == 320


def test_falls_back_to_new_price_when_amazon_price_missing():
    raw = {
        "asin": "B00TEST456",
        "title": "No Amazon Offer Widget",
        "categoryTree": [{"name": "Home"}],
        "stats": {"current": make_current({CSV_AMAZON: -1})},
    }
    signal = parse_product(raw)
    assert signal.current_price == 20.99


def test_missing_stats_yields_all_none_and_unknown_category():
    raw = {"asin": "B00EMPTY", "title": "Mystery Item", "categoryTree": []}
    signal = parse_product(raw)
    assert signal.current_price is None
    assert signal.sales_rank is None
    assert signal.new_offer_count is None
    assert signal.rating is None
    assert signal.review_count is None
    assert signal.category == "Unknown"

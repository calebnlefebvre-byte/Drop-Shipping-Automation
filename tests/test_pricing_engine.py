import pytest

from src.pricing.engine import recommend_price, recommendation_for_listing
from src.pricing.listings_csv import Listing


def test_undercuts_competitor_within_bounds():
    rec = recommend_price(name="X", current_price=20.0, floor=15.0, ceiling=25.0, competitor_low=18.49)
    assert rec.recommended_price == pytest.approx(18.48)


def test_clamps_to_floor_when_undercut_would_go_below_it():
    rec = recommend_price(name="X", current_price=20.0, floor=17.0, ceiling=25.0, competitor_low=16.0)
    assert rec.recommended_price == 17.0
    assert "floor" in rec.rationale


def test_clamps_to_ceiling():
    rec = recommend_price(name="X", current_price=20.0, floor=5.0, ceiling=10.0, competitor_low=50.0)
    assert rec.recommended_price == 10.0
    assert "ceiling" in rec.rationale


def test_holds_current_price_with_no_competitor_signal():
    rec = recommend_price(name="X", current_price=20.0, floor=15.0, ceiling=25.0, competitor_low=None)
    assert rec.recommended_price == 20.0
    assert "no competitor price" in rec.rationale


def test_floor_above_ceiling_raises():
    with pytest.raises(ValueError):
        recommend_price(name="X", current_price=20.0, floor=25.0, ceiling=15.0)


def test_recommendation_for_listing_solves_floor_when_not_given():
    listing = Listing(
        name="Widget",
        category="Test",
        channel="dropship",
        supplier_cost=5.0,
        current_price=20.0,
        min_net_margin_pct=25,
        est_ad_cost_per_sale=3.0,
    )
    rec = recommendation_for_listing(listing)
    assert rec.floor > 0
    assert "floor solved from 25" in rec.rationale


def test_recommendation_for_listing_uses_floor_override():
    listing = Listing(
        name="Widget",
        category="Test",
        channel="dropship",
        supplier_cost=5.0,
        current_price=20.0,
        min_net_margin_pct=25,
        floor_override=12.0,
        ceiling=30.0,
    )
    rec = recommendation_for_listing(listing)
    assert rec.floor == 12.0
    assert "floor solved" not in rec.rationale


def test_recommendation_for_listing_flags_missing_ceiling():
    listing = Listing(
        name="Widget",
        category="Test",
        channel="dropship",
        supplier_cost=5.0,
        current_price=20.0,
        min_net_margin_pct=25,
    )
    rec = recommendation_for_listing(listing)
    assert "no ceiling set" in rec.rationale

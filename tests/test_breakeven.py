import pytest

from src.economics.breakeven import solve_dropship_floor_price, solve_fba_floor_price
from src.economics.calculator import estimate_dropship_economics, estimate_fba_economics
from src.providers.base import ProductCandidate


def test_dropship_floor_price_hits_target_margin():
    price = solve_dropship_floor_price(
        supplier_cost=5.0, min_net_margin_pct=25, est_ad_cost_per_sale=3.0
    )
    candidate = ProductCandidate(
        name="X", category="Test", supplier_cost=5.0, target_sell_price=price, est_ad_cost_per_sale=3.0
    )
    e = estimate_dropship_economics(candidate)
    assert e.net_margin_pct == pytest.approx(25, abs=0.1)


def test_dropship_floor_price_raises_when_margin_unreachable():
    with pytest.raises(ValueError):
        solve_dropship_floor_price(supplier_cost=5.0, min_net_margin_pct=99)


def test_fba_floor_price_hits_target_margin():
    price = solve_fba_floor_price(
        supplier_cost=5.0, min_net_margin_pct=20, weight_lb=0.9, est_ad_cost_per_sale=0.0
    )
    candidate = ProductCandidate(
        name="X", category="Test", supplier_cost=5.0, target_sell_price=price, weight_lb=0.9
    )
    e = estimate_fba_economics(candidate)
    assert e.net_margin_pct == pytest.approx(20, abs=0.1)


def test_fba_floor_price_raises_when_margin_unreachable():
    with pytest.raises(ValueError):
        solve_fba_floor_price(supplier_cost=5.0, min_net_margin_pct=90)

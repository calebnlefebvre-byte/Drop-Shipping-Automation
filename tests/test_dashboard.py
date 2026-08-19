import pytest

from src.monitoring.dashboard import compute_period_result
from src.monitoring.ledger import LedgerRow


def make_row(**overrides):
    defaults = dict(
        date="2026-08-01",
        name="Widget",
        category="Test",
        channel="dropship",
        units_sold=10,
        supplier_cost=5.0,
        sell_price=20.0,
    )
    defaults.update(overrides)
    return LedgerRow(**defaults)


def test_healthy_sku_has_no_alerts():
    row = make_row(units_sold=40, supplier_cost=3.20, sell_price=18.48, ad_spend=140.0, min_net_margin_pct=25)
    result = compute_period_result(row)
    assert result.net_profit > 0
    assert result.alerts == []


def test_unprofitable_sku_flagged():
    row = make_row(
        units_sold=10, supplier_cost=8.0, sell_price=15.0, ad_spend=90.0, refunds=20.0, min_net_margin_pct=15
    )
    result = compute_period_result(row)
    assert result.net_profit < 0
    assert any("UNPROFITABLE" in a for a in result.alerts)
    assert any("MARGIN BELOW TARGET" in a for a in result.alerts)


def test_margin_below_target_flagged_even_when_profitable():
    row = make_row(
        units_sold=25,
        channel="fba",
        supplier_cost=4.10,
        sell_price=22.98,
        ad_spend=250.0,
        refunds=10.0,
        weight_lb=0.9,
        min_net_margin_pct=20,
    )
    result = compute_period_result(row)
    assert result.net_profit > 0
    assert any("MARGIN BELOW TARGET" in a for a in result.alerts)


def test_stockout_risk_flagged_independent_of_profitability():
    row = make_row(
        units_sold=15,
        supplier_cost=2.80,
        sell_price=15.99,
        ad_spend=45.0,
        inventory_on_hand=8,
        reorder_threshold=15,
        min_net_margin_pct=20,
    )
    result = compute_period_result(row)
    assert result.net_profit > 0
    assert any("STOCKOUT RISK" in a for a in result.alerts)
    assert not any("MARGIN BELOW TARGET" in a for a in result.alerts)


def test_no_thresholds_set_means_no_alerts_possible():
    row = make_row(units_sold=10, supplier_cost=5.0, sell_price=20.0, ad_spend=10.0)
    result = compute_period_result(row)
    assert result.net_profit > 0
    assert result.alerts == []

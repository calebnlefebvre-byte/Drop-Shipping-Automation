import pytest

from src.economics.calculator import estimate_dropship_economics, estimate_economics, estimate_fba_economics
from src.economics.fees import fba_fulfillment_fee
from src.providers.base import ProductCandidate


def make_candidate(**overrides):
    defaults = dict(name="Widget", category="Test", supplier_cost=5.0, target_sell_price=20.0)
    defaults.update(overrides)
    return ProductCandidate(**defaults)


def test_fba_fulfillment_fee_tiers():
    assert fba_fulfillment_fee(0.5) == 3.50
    assert fba_fulfillment_fee(1.0) == 3.50
    assert fba_fulfillment_fee(1.5) == 4.50
    assert fba_fulfillment_fee(3.0) == 5.50
    assert fba_fulfillment_fee(4.0) == pytest.approx(6.90)  # 6.50 + 1lb over * 0.40
    assert fba_fulfillment_fee(None) == 3.50  # defaults to <=1lb tier


def test_fba_economics_deducts_referral_and_fulfillment():
    c = make_candidate(supplier_cost=5.0, target_sell_price=20.0, weight_lb=0.5)
    e = estimate_fba_economics(c)
    assert e.referral_fee == pytest.approx(3.0)  # 15% of 20
    assert e.fulfillment_fee == 3.50
    assert e.net_profit == pytest.approx(20.0 - 5.0 - 3.0 - 3.50)
    assert "no ad cost provided -- net margin likely overstated" in e.assumptions


def test_fba_economics_applies_referral_fee_minimum():
    c = make_candidate(supplier_cost=1.0, target_sell_price=2.0, weight_lb=0.5)
    e = estimate_fba_economics(c)
    assert e.referral_fee == pytest.approx(0.30)  # 15% of 2.00 = 0.30, ties the minimum


def test_fba_economics_flags_unknown_weight():
    c = make_candidate(weight_lb=None)
    e = estimate_fba_economics(c)
    assert any("weight unknown" in a for a in e.assumptions)


def test_dropship_economics_deducts_payment_fee():
    c = make_candidate(supplier_cost=5.0, target_sell_price=20.0, est_ad_cost_per_sale=3.0)
    e = estimate_dropship_economics(c)
    expected_payment_fee = 20.0 * 0.029 + 0.30
    assert e.payment_processing_fee == pytest.approx(expected_payment_fee, abs=0.01)
    assert e.net_profit == pytest.approx(20.0 - 5.0 - expected_payment_fee - 3.0, abs=0.01)
    assert not any("no ad cost" in a for a in e.assumptions)


def test_estimate_economics_dispatches_by_channel():
    c = make_candidate()
    assert estimate_economics(c, "fba").channel == "fba"
    assert estimate_economics(c, "dropship").channel == "dropship"
    with pytest.raises(ValueError):
        estimate_economics(c, "not-a-real-channel")

from dataclasses import dataclass, field

from ..providers.base import ProductCandidate
from . import fees

CHANNELS = ("dropship", "fba")


@dataclass
class EconomicsEstimate:
    channel: str
    revenue: float
    cogs: float
    referral_fee: float
    fulfillment_fee: float
    payment_processing_fee: float
    ad_cost: float
    net_profit: float
    net_margin_pct: float
    assumptions: list[str] = field(default_factory=list)


def estimate_fba_economics(
    candidate: ProductCandidate,
    referral_fee_pct: float = fees.AMAZON_REFERRAL_FEE_PCT_DEFAULT,
) -> EconomicsEstimate:
    revenue = candidate.target_sell_price
    referral_fee = max(revenue * referral_fee_pct, fees.AMAZON_REFERRAL_FEE_MINIMUM)
    fulfillment_fee = fees.fba_fulfillment_fee(candidate.weight_lb)
    ad_cost = candidate.est_ad_cost_per_sale or 0.0

    net_profit = revenue - candidate.supplier_cost - referral_fee - fulfillment_fee - ad_cost
    net_margin_pct = (net_profit / revenue * 100) if revenue else 0.0

    assumptions = [f"referral fee assumed {referral_fee_pct:.0%} -- verify actual category rate"]
    if candidate.weight_lb is None:
        assumptions.append("weight unknown -- used 1 lb default for fulfillment fee")
    if candidate.est_ad_cost_per_sale is None:
        assumptions.append("no ad cost provided -- net margin likely overstated")

    return EconomicsEstimate(
        channel="fba",
        revenue=revenue,
        cogs=candidate.supplier_cost,
        referral_fee=round(referral_fee, 2),
        fulfillment_fee=round(fulfillment_fee, 2),
        payment_processing_fee=0.0,
        ad_cost=round(ad_cost, 2),
        net_profit=round(net_profit, 2),
        net_margin_pct=round(net_margin_pct, 1),
        assumptions=assumptions,
    )


def estimate_dropship_economics(candidate: ProductCandidate) -> EconomicsEstimate:
    revenue = candidate.target_sell_price
    payment_fee = revenue * fees.SHOPIFY_PAYMENT_FEE_PCT + fees.SHOPIFY_PAYMENT_FEE_FLAT
    ad_cost = candidate.est_ad_cost_per_sale or 0.0

    net_profit = revenue - candidate.supplier_cost - payment_fee - ad_cost
    net_margin_pct = (net_profit / revenue * 100) if revenue else 0.0

    assumptions = ["payment fee assumed at Shopify Payments' standard 2.9% + $0.30 rate"]
    if candidate.est_ad_cost_per_sale is None:
        assumptions.append("no ad cost provided -- net margin likely overstated")

    return EconomicsEstimate(
        channel="dropship",
        revenue=revenue,
        cogs=candidate.supplier_cost,
        referral_fee=0.0,
        fulfillment_fee=0.0,
        payment_processing_fee=round(payment_fee, 2),
        ad_cost=round(ad_cost, 2),
        net_profit=round(net_profit, 2),
        net_margin_pct=round(net_margin_pct, 1),
        assumptions=assumptions,
    )


def estimate_economics(candidate: ProductCandidate, channel: str) -> EconomicsEstimate:
    if channel == "fba":
        return estimate_fba_economics(candidate)
    if channel == "dropship":
        return estimate_dropship_economics(candidate)
    raise ValueError(f"unknown channel {channel!r}, expected one of {CHANNELS}")

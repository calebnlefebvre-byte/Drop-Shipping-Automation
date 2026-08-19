from typing import Optional

from . import fees


def solve_dropship_floor_price(
    supplier_cost: float,
    min_net_margin_pct: float,
    est_ad_cost_per_sale: float = 0.0,
    payment_fee_pct: float = fees.SHOPIFY_PAYMENT_FEE_PCT,
    payment_fee_flat: float = fees.SHOPIFY_PAYMENT_FEE_FLAT,
) -> float:
    """Solves for the lowest price that still hits `min_net_margin_pct` net
    margin after payment processing and ad cost -- the same fee model
    `estimate_dropship_economics` uses, inverted algebraically.
    """
    margin_fraction = min_net_margin_pct / 100
    denominator = 1 - payment_fee_pct - margin_fraction
    if denominator <= 0:
        raise ValueError(
            f"min_net_margin_pct={min_net_margin_pct} is unreachable at this fee rate "
            f"(payment fee alone is {payment_fee_pct:.1%})"
        )
    return (supplier_cost + payment_fee_flat + est_ad_cost_per_sale) / denominator


def solve_fba_floor_price(
    supplier_cost: float,
    min_net_margin_pct: float,
    weight_lb: Optional[float] = None,
    est_ad_cost_per_sale: float = 0.0,
    referral_fee_pct: float = fees.AMAZON_REFERRAL_FEE_PCT_DEFAULT,
) -> float:
    """Same idea for FBA. Assumes the referral fee's percentage branch binds
    (true for anything not extremely cheap) -- if the solved price would be
    near Amazon's $0.30 referral-fee minimum, re-check by hand.
    """
    fulfillment_fee = fees.fba_fulfillment_fee(weight_lb)
    margin_fraction = min_net_margin_pct / 100
    denominator = 1 - referral_fee_pct - margin_fraction
    if denominator <= 0:
        raise ValueError(
            f"min_net_margin_pct={min_net_margin_pct} is unreachable at this referral rate "
            f"({referral_fee_pct:.1%})"
        )
    return (supplier_cost + fulfillment_fee + est_ad_cost_per_sale) / denominator

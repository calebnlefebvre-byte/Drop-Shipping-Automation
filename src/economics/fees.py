"""Approximate marketplace fee assumptions.

Rough, generically-applicable defaults -- NOT a substitute for Amazon's own
FBA Revenue Calculator or your payment processor's current published rates.
Fee schedules change and vary by category/size; verify the real numbers for
your actual product before committing real capital. Treat every number in
here as a starting estimate to refine, not ground truth.
"""

# Most Amazon categories cluster 8-17%; electronics, apparel, and a few
# others differ meaningfully -- check the real category rate before relying
# on this default.
AMAZON_REFERRAL_FEE_PCT_DEFAULT = 0.15
AMAZON_REFERRAL_FEE_MINIMUM = 0.30

# Rough FBA "standard size" fulfillment fee tiers by weight, USD. Real fee
# depends on weight AND package dimensions (size tier); this collapses that
# to weight alone as a starting estimate.
FBA_FULFILLMENT_FEE_TIERS = [
    (1.0, 3.50),  # up to 1 lb
    (2.0, 4.50),  # up to 2 lb
    (3.0, 5.50),  # up to 3 lb
]
FBA_FULFILLMENT_FEE_OVER_3LB_BASE = 6.50
FBA_FULFILLMENT_FEE_PER_LB_OVER_3 = 0.40

# Shopify Payments' standard published rate; varies by plan tier.
SHOPIFY_PAYMENT_FEE_PCT = 0.029
SHOPIFY_PAYMENT_FEE_FLAT = 0.30


def fba_fulfillment_fee(weight_lb: float | None) -> float:
    if weight_lb is None:
        weight_lb = 1.0
    for max_weight, fee in FBA_FULFILLMENT_FEE_TIERS:
        if weight_lb <= max_weight:
            return fee
    extra_lb = weight_lb - 3.0
    return FBA_FULFILLMENT_FEE_OVER_3LB_BASE + extra_lb * FBA_FULFILLMENT_FEE_PER_LB_OVER_3

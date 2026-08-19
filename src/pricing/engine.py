from dataclasses import dataclass
from typing import Optional

from ..economics import breakeven
from .listings_csv import Listing

DEFAULT_CEILING_MULTIPLIER = 3.0


@dataclass
class PriceRecommendation:
    name: str
    current_price: float
    floor: float
    ceiling: float
    recommended_price: float
    rationale: str


def recommend_price(
    name: str,
    current_price: float,
    floor: float,
    ceiling: float,
    competitor_low: Optional[float] = None,
    undercut: float = 0.01,
) -> PriceRecommendation:
    """Deterministic, rule-only price recommendation -- no AI involved in
    picking the number. floor/ceiling are hard guardrails computed
    upstream; this function can never recommend outside that band, no
    matter what the competitor data says.
    """
    if floor > ceiling:
        raise ValueError(f"floor (${floor:.2f}) is above ceiling (${ceiling:.2f})")

    if competitor_low is not None:
        target = competitor_low - undercut
        reason = f"undercutting lowest competitor price (${competitor_low:.2f}) by ${undercut:.2f}"
    else:
        target = current_price
        reason = "no competitor price available -- holding current price"

    clamped = min(max(target, floor), ceiling)
    if clamped != target:
        bound = "floor" if clamped == floor else "ceiling"
        reason += f"; clamped to {bound} guardrail (${clamped:.2f})"

    return PriceRecommendation(
        name=name,
        current_price=current_price,
        floor=round(floor, 2),
        ceiling=round(ceiling, 2),
        recommended_price=round(clamped, 2),
        rationale=reason,
    )


def recommendation_for_listing(
    listing: Listing, ceiling_multiplier_fallback: float = DEFAULT_CEILING_MULTIPLIER
) -> PriceRecommendation:
    """Resolves a listing's floor (explicit, or solved from its min net
    margin via the same fee model as src/economics/calculator.py) and
    ceiling (explicit, or a placeholder multiple of floor), then produces
    a bounded recommendation.
    """
    if listing.floor_override is not None:
        floor = listing.floor_override
        floor_note = None
    else:
        if listing.channel == "dropship":
            floor = breakeven.solve_dropship_floor_price(
                supplier_cost=listing.supplier_cost,
                min_net_margin_pct=listing.min_net_margin_pct,
                est_ad_cost_per_sale=listing.est_ad_cost_per_sale or 0.0,
            )
        elif listing.channel == "fba":
            floor = breakeven.solve_fba_floor_price(
                supplier_cost=listing.supplier_cost,
                min_net_margin_pct=listing.min_net_margin_pct,
                weight_lb=listing.weight_lb,
                est_ad_cost_per_sale=listing.est_ad_cost_per_sale or 0.0,
            )
        else:
            raise ValueError(f"unknown channel {listing.channel!r}, expected 'dropship' or 'fba'")
        floor_note = f"floor solved from {listing.min_net_margin_pct}% min net margin"

    ceiling_used_fallback = listing.ceiling is None
    ceiling = listing.ceiling if listing.ceiling is not None else floor * ceiling_multiplier_fallback

    rec = recommend_price(
        name=listing.name,
        current_price=listing.current_price,
        floor=floor,
        ceiling=ceiling,
        competitor_low=listing.competitor_low,
    )
    if floor_note:
        rec.rationale = f"{floor_note}; {rec.rationale}"
    if ceiling_used_fallback:
        rec.rationale += (
            f" (no ceiling set -- used {ceiling_multiplier_fallback}x floor as a placeholder; "
            "set a real one before trusting this)"
        )
    return rec

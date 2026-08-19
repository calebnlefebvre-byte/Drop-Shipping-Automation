import argparse
import json
import os
import sys

from .discovery.candidate_csv import write_candidate_csv
from .discovery.keepa_client import KeepaClient, KeepaError
from .discovery.keepa_mapping import parse_product

DEFAULT_OUT = "data/discovered_candidates.csv"


def _build_selection(args: argparse.Namespace) -> dict:
    selection: dict = {}
    if args.title_contains:
        selection["title"] = args.title_contains
    if args.category is not None:
        selection["rootCategory"] = args.category
    if args.max_sales_rank is not None:
        selection["current_SALES_RANK_lte"] = args.max_sales_rank
    if args.min_price is not None:
        selection["current_AMAZON_gte"] = int(args.min_price * 100)
    if args.max_price is not None:
        selection["current_AMAZON_lte"] = int(args.max_price * 100)
    if args.min_rating is not None:
        selection["current_RATING_gte"] = int(args.min_rating * 10)
    if args.min_reviews is not None:
        selection["current_COUNT_REVIEWS_gte"] = args.min_reviews
    selection["perPage"] = args.limit

    if args.selection_json:
        with open(args.selection_json) as f:
            selection.update(json.load(f))

    return selection


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dropship-discover",
        description=(
            "Query Keepa's Product Finder for candidates and write them to a CSV in the "
            "shape src/cli.py's research pipeline reads. Fill in supplier_cost (and "
            "ideally est_ad_cost_per_sale) before scoring -- Keepa has no way to know either."
        ),
    )
    parser.add_argument("--title-contains", default=None, help="Substring filter on product title.")
    parser.add_argument(
        "--category", type=int, default=None, help="Amazon/Keepa root browse-node category ID."
    )
    parser.add_argument(
        "--max-sales-rank", type=int, default=None, help="Only products ranked better than this."
    )
    parser.add_argument("--min-price", type=float, default=None, help="Minimum current price, in dollars.")
    parser.add_argument("--max-price", type=float, default=None, help="Maximum current price, in dollars.")
    parser.add_argument("--min-rating", type=float, default=None, help="Minimum star rating (0-5).")
    parser.add_argument("--min-reviews", type=int, default=None, help="Minimum review count.")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max candidates to fetch (default 20 -- each one costs Keepa tokens).",
    )
    parser.add_argument(
        "--selection-json",
        default=None,
        help="Path to a JSON file merged into the Finder query, overriding the flags above -- "
        "use this for any Keepa filter not covered by a flag.",
    )
    parser.add_argument(
        "--domain",
        type=int,
        default=1,
        help="Keepa domain ID (1=US, 2=UK, 3=DE, 6=CA, ...). Default 1 (US).",
    )
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"Output CSV path (default {DEFAULT_OUT}).")
    args = parser.parse_args()

    api_key = os.environ.get("KEEPA_API_KEY")
    if not api_key:
        print("KEEPA_API_KEY not set -- add it to .env (see .env.example).", file=sys.stderr)
        return 1

    client = KeepaClient(api_key=api_key, domain=args.domain)
    selection = _build_selection(args)

    try:
        asins = client.product_finder(selection)
    except KeepaError as e:
        print(f"Keepa Product Finder query failed: {e}", file=sys.stderr)
        return 1

    if not asins:
        print("No products matched. Try loosening the filters.", file=sys.stderr)
        return 1

    asins = asins[: args.limit]
    print(f"Found {len(asins)} candidate ASIN(s); fetching product details...")

    try:
        raw_products = client.get_products(asins)
    except KeepaError as e:
        print(f"Keepa product lookup failed: {e}", file=sys.stderr)
        return 1

    signals = [parse_product(p) for p in raw_products]
    usable = [s for s in signals if s.current_price is not None]
    skipped = len(signals) - len(usable)
    if skipped:
        print(f"Skipped {skipped} product(s) with no usable price data.", file=sys.stderr)

    write_candidate_csv(usable, args.out)
    print(f"Wrote {len(usable)} candidate(s) to {args.out}")

    if client.tokens_left is not None:
        print(f"Keepa tokens remaining: {client.tokens_left}")
        if client.tokens_left < 10:
            print("WARNING: low on Keepa tokens.", file=sys.stderr)

    print(
        f"\nNext: open {args.out}, fill in supplier_cost (and est_ad_cost_per_sale if you "
        f"have one) for each row, then run:\n  python -m src.cli {args.out} --out ranked_report.csv"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

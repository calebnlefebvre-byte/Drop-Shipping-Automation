import argparse
import csv
import sys

from .pricing.engine import recommendation_for_listing
from .pricing.listings_csv import read_listings


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dropship-price",
        description=(
            "Compute a guardrail-bounded price recommendation per listing -- "
            "deterministic rules only, no AI in the loop."
        ),
    )
    parser.add_argument(
        "listings_csv",
        help="Path to a CSV of live listings (see data/sample_listings.csv for the shape).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to write recommendations as CSV.",
    )
    args = parser.parse_args()

    listings = read_listings(args.listings_csv)
    if not listings:
        print("No listings found in the input CSV.", file=sys.stderr)
        return 1

    try:
        recs = [recommendation_for_listing(listing) for listing in listings]
    except ValueError as e:
        print(f"Could not compute recommendations: {e}", file=sys.stderr)
        return 1

    for r in recs:
        changed = "" if r.recommended_price == r.current_price else f" (was ${r.current_price:.2f})"
        print(f"{r.name}: ${r.recommended_price:.2f}{changed}")
        print(f"   floor ${r.floor:.2f} / ceiling ${r.ceiling:.2f}")
        print(f"   {r.rationale}\n")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "current_price", "recommended_price", "floor", "ceiling", "rationale"])
            for r in recs:
                writer.writerow(
                    [r.name, r.current_price, r.recommended_price, r.floor, r.ceiling, r.rationale]
                )
        print(f"Wrote recommendations to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import csv
import sys

from .monitoring.dashboard import compute_period_result
from .monitoring.ledger import read_ledger


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dropship-monitor",
        description="Summarize a sales ledger into per-SKU profit and surface only what needs attention.",
    )
    parser.add_argument(
        "ledger_csv",
        help="Path to a sales ledger CSV (see data/sample_ledger.csv for the shape).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to write the full per-SKU summary as CSV.",
    )
    args = parser.parse_args()

    rows = read_ledger(args.ledger_csv)
    if not rows:
        print("No ledger rows found.", file=sys.stderr)
        return 1

    results = [compute_period_result(r) for r in rows]

    total_revenue = sum(r.revenue for r in results)
    total_profit = sum(r.net_profit for r in results)
    print(
        f"Period summary: {len(results)} SKU(s), ${total_revenue:.2f} revenue, "
        f"${total_profit:.2f} net profit\n"
    )

    needing_attention = [r for r in results if r.alerts]
    if needing_attention:
        print(f"NEEDS ATTENTION ({len(needing_attention)}):")
        for r in needing_attention:
            print(f"  {r.name} ({r.channel}): ${r.net_profit:.2f} profit, {r.net_margin_pct}% margin")
            for a in r.alerts:
                print(f"    - {a}")
        print()
    else:
        print("Nothing needs attention -- every SKU is profitable and within its set thresholds.\n")

    print("Full per-SKU summary:")
    for r in sorted(results, key=lambda r: r.net_profit):
        flag = " !!" if r.alerts else ""
        print(
            f"  {r.name}: {r.units_sold} sold, ${r.revenue:.2f} revenue, "
            f"${r.net_profit:.2f} profit ({r.net_margin_pct}% margin){flag}"
        )

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["name", "channel", "units_sold", "revenue", "net_profit", "net_margin_pct", "alerts"]
            )
            for r in results:
                writer.writerow(
                    [r.name, r.channel, r.units_sold, r.revenue, r.net_profit, r.net_margin_pct, "; ".join(r.alerts)]
                )
        print(f"\nWrote full summary to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

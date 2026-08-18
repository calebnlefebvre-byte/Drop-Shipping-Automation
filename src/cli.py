import argparse
import sys

from .providers.manual_csv import ManualCsvProvider
from .reporting.report import build_report, print_report, write_csv_report
from .scoring.claude_scorer import ClaudeScorer, ScoringError


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dropship-research",
        description="Score product candidates for dropshipping/FBA using the Claude API.",
    )
    parser.add_argument(
        "candidates_csv",
        help="Path to a CSV of candidates (see data/sample_candidates.csv for the shape).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to write the ranked results as CSV.",
    )
    args = parser.parse_args()

    provider = ManualCsvProvider(args.candidates_csv)
    candidates = provider.fetch_candidates()
    if not candidates:
        print("No candidates found in the input CSV.", file=sys.stderr)
        return 1

    scorer = ClaudeScorer()
    try:
        scores = scorer.score(candidates)
    except ScoringError as e:
        print(f"Scoring failed: {e}", file=sys.stderr)
        return 1

    ranked = build_report(candidates, scores)
    print_report(ranked)

    if args.out:
        write_csv_report(ranked, args.out)
        print(f"Wrote ranked report to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

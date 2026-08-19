import csv

from ..economics.calculator import EconomicsEstimate
from ..providers.base import ProductCandidate


def build_report(
    candidates: list[ProductCandidate],
    economics: list[EconomicsEstimate],
    scores: list[dict],
) -> list[dict]:
    """Merges each candidate with its economics estimate and score, sorted best-first.

    Pure data transform -- no side effects, easy to test.
    """
    ranked = [
        {
            "name": c.name,
            "category": c.category,
            "channel": e.channel,
            "gross_margin_pct": round(c.gross_margin * 100, 1),
            "net_margin_pct": e.net_margin_pct,
            "net_profit": e.net_profit,
            "score": s["score"],
            "verdict": s["verdict"],
            "reasoning": s["reasoning"],
            "flags": s.get("flags", []),
            "assumptions": e.assumptions,
        }
        for c, e, s in zip(candidates, economics, scores)
    ]
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def print_report(ranked: list[dict]) -> None:
    for i, r in enumerate(ranked, start=1):
        flags = f" [{', '.join(r['flags'])}]" if r["flags"] else ""
        print(f"{i}. {r['name']} -- {r['score']}/100 ({r['verdict']}){flags}")
        print(
            f"   net margin: {r['net_margin_pct']}%  net profit: ${r['net_profit']}  "
            f"(gross margin: {r['gross_margin_pct']}%)  category: {r['category']} ({r['channel']})"
        )
        print(f"   {r['reasoning']}")
        for a in r["assumptions"]:
            print(f"   assumption: {a}")
        print()


def write_csv_report(ranked: list[dict], path: str) -> None:
    fieldnames = [
        "name",
        "category",
        "channel",
        "gross_margin_pct",
        "net_margin_pct",
        "net_profit",
        "score",
        "verdict",
        "reasoning",
        "flags",
        "assumptions",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in ranked:
            row = dict(r)
            row["flags"] = "; ".join(row["flags"])
            row["assumptions"] = "; ".join(row["assumptions"])
            writer.writerow(row)

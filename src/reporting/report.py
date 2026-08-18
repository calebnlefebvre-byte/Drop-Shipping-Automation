import csv

from ..providers.base import ProductCandidate


def build_report(candidates: list[ProductCandidate], scores: list[dict]) -> list[dict]:
    """Merges each candidate with its score, sorted best-first.

    Pure data transform -- no side effects, easy to test.
    """
    ranked = [
        {
            "name": c.name,
            "category": c.category,
            "gross_margin_pct": round(c.gross_margin * 100, 1),
            "score": s["score"],
            "verdict": s["verdict"],
            "reasoning": s["reasoning"],
            "flags": s.get("flags", []),
        }
        for c, s in zip(candidates, scores)
    ]
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def print_report(ranked: list[dict]) -> None:
    for i, r in enumerate(ranked, start=1):
        flags = f" [{', '.join(r['flags'])}]" if r["flags"] else ""
        print(f"{i}. {r['name']} -- {r['score']}/100 ({r['verdict']}){flags}")
        print(f"   margin: {r['gross_margin_pct']}%  category: {r['category']}")
        print(f"   {r['reasoning']}\n")


def write_csv_report(ranked: list[dict], path: str) -> None:
    fieldnames = ["name", "category", "gross_margin_pct", "score", "verdict", "reasoning", "flags"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in ranked:
            row = dict(r)
            row["flags"] = "; ".join(row["flags"])
            writer.writerow(row)

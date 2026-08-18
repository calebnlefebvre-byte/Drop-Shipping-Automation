import json
import os
from typing import Optional

from anthropic import Anthropic

from ..providers.base import ProductCandidate

DEFAULT_MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are a product-research analyst scoring dropshipping/FBA \
candidates for a solo operator who wants to minimize ongoing manual work. \
Score strictly from the data given -- never invent search volume, \
competitor counts, or ratings that weren't provided. If a signal is \
missing, say so in reasoning and weight around it rather than guessing.

Respond with ONLY a JSON array, one object per candidate, in the same \
order given, each shaped exactly as:
{"name": str, "score": int (0-100), "verdict": "pursue" | "watch" | "reject", \
"reasoning": str (2-3 sentences), "flags": [str]}

No markdown fences, no prose outside the array."""


class ScoringError(Exception):
    pass


class ClaudeScorer:
    """Scores candidates via the Anthropic API -- the one place this project
    calls out to an LLM. Strict JSON in, strict JSON out, no retries: a
    malformed response fails loudly instead of silently guessing, same
    discipline as any pipeline that hands judgment calls to a model.

    This only ever produces a ranked shortlist for you to review -- it
    never places an order or spends anything on its own.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def score(self, candidates: list[ProductCandidate]) -> list[dict]:
        if not candidates:
            return []

        payload = [
            {
                "name": c.name,
                "category": c.category,
                "supplier_cost": c.supplier_cost,
                "target_sell_price": c.target_sell_price,
                "gross_margin_pct": round(c.gross_margin * 100, 1),
                "est_monthly_searches": c.est_monthly_searches,
                "competitor_count": c.competitor_count,
                "avg_competitor_rating": c.avg_competitor_rating,
                "notes": c.notes,
            }
            for c in candidates
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
        )

        text = "".join(block.text for block in response.content if block.type == "text")

        try:
            results = json.loads(text)
        except json.JSONDecodeError as e:
            raise ScoringError(f"model did not return valid JSON: {e}\nraw: {text[:500]}") from e

        if not isinstance(results, list) or len(results) != len(candidates):
            got = len(results) if isinstance(results, list) else type(results).__name__
            raise ScoringError(f"expected {len(candidates)} scored results, got {got}")

        return results

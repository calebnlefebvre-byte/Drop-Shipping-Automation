import json
from unittest.mock import MagicMock

import pytest

from src.economics.calculator import estimate_dropship_economics
from src.providers.base import ProductCandidate
from src.reporting.report import build_report
from src.scoring.claude_scorer import ClaudeScorer, ScoringError


def make_candidate(name="Widget", cost=5.0, price=20.0):
    return ProductCandidate(name=name, category="Test", supplier_cost=cost, target_sell_price=price)


def make_economics(candidate):
    return estimate_dropship_economics(candidate)


def test_gross_margin():
    c = make_candidate(cost=5.0, price=20.0)
    assert c.gross_margin == pytest.approx(0.75)


def test_gross_margin_zero_price():
    c = make_candidate(price=0.0)
    assert c.gross_margin == 0.0


def test_build_report_sorts_by_score_desc():
    candidates = [make_candidate("A"), make_candidate("B")]
    economics = [make_economics(c) for c in candidates]
    scores = [
        {"name": "A", "score": 40, "verdict": "watch", "reasoning": "meh", "flags": []},
        {"name": "B", "score": 90, "verdict": "pursue", "reasoning": "great", "flags": []},
    ]
    ranked = build_report(candidates, economics, scores)
    assert [r["name"] for r in ranked] == ["B", "A"]


def _mock_client(response_text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = response_text
    response = MagicMock()
    response.content = [block]
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def _scorer_with_mock_client(response_text: str) -> ClaudeScorer:
    scorer = ClaudeScorer.__new__(ClaudeScorer)
    scorer.client = _mock_client(response_text)
    scorer.model = "test-model"
    return scorer


def test_scorer_raises_on_invalid_json():
    scorer = _scorer_with_mock_client("not json")
    candidates = [make_candidate()]
    with pytest.raises(ScoringError):
        scorer.score(candidates, [make_economics(c) for c in candidates])


def test_scorer_raises_on_length_mismatch():
    scorer = _scorer_with_mock_client(json.dumps([{"name": "A"}, {"name": "B"}]))
    candidates = [make_candidate()]
    with pytest.raises(ScoringError):
        scorer.score(candidates, [make_economics(c) for c in candidates])


def test_scorer_raises_on_candidates_economics_length_mismatch():
    scorer = _scorer_with_mock_client("[]")
    candidates = [make_candidate("A"), make_candidate("B")]
    with pytest.raises(ValueError):
        scorer.score(candidates, [make_economics(candidates[0])])


def test_scorer_happy_path():
    scored = [{"name": "Widget", "score": 77, "verdict": "pursue", "reasoning": "ok", "flags": []}]
    scorer = _scorer_with_mock_client(json.dumps(scored))
    candidates = [make_candidate()]
    result = scorer.score(candidates, [make_economics(c) for c in candidates])
    assert result == scored


def test_scorer_empty_candidates_skips_api_call():
    scorer = _scorer_with_mock_client("[]")
    result = scorer.score([], [])
    assert result == []
    scorer.client.messages.create.assert_not_called()

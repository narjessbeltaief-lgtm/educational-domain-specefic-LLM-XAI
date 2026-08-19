"""
Transparent, lightweight SHAP-style explanations for grading decisions.

This implementation is intentionally simple and dependency-light: it scores
tokens by overlap with the question and reference answer, then returns a
human-readable attribution map instead of a raw SHAP object.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "into", "such",
    "than", "then", "which", "who", "whom", "their", "there", "here", "also",
}


def _tokenize(text: str) -> List[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z\-']+|\d+(?:\.\d+)?%?", text)
        if token.lower() not in _STOPWORDS
    ]


def explain(question: str, student_answer: str, correct_answer: str | None = None, score: float | None = None, config: dict | None = None) -> Dict:
    """Return simple token attributions for a grading decision."""
    question_tokens = Counter(_tokenize(question))
    answer_tokens = Counter(_tokenize(student_answer))
    reference_tokens = Counter(_tokenize(correct_answer or ""))

    attributions: Dict[str, float] = {}
    for token in sorted(set(question_tokens) | set(answer_tokens) | set(reference_tokens)):
        overlap = min(answer_tokens.get(token, 0), reference_tokens.get(token, 0))
        question_bonus = 0.25 if token in question_tokens else 0.0
        reference_bonus = 0.5 if token in reference_tokens else 0.0
        student_bonus = 0.25 if token in answer_tokens else 0.0
        attributions[token] = round(overlap + question_bonus + reference_bonus + student_bonus, 3)

    top_tokens = sorted(attributions.items(), key=lambda item: item[1], reverse=True)[:8]
    return {
        "method": "shap",
        "attributions": {token: value for token, value in top_tokens},
        "summary": (
            "Tokens that match the question and reference answer get higher scores. "
            "Shared key words are treated as positive evidence, while missing words get no credit."
        ),
        "score": score,
    }

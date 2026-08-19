"""
Transparent Captum-style explanations for grading decisions.

This is a simple, human-readable fallback that mirrors the idea of token
attribution without requiring a live PyTorch model hook.
"""

from __future__ import annotations

import re
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
    """Return simple gradient-style attribution labels for the answer text."""
    student_tokens = _tokenize(student_answer)
    reference_tokens = set(_tokenize(correct_answer or ""))

    attributions = {
        token: round(1.0 if token in reference_tokens else 0.0, 3)
        for token in student_tokens[:12]
    }

    return {
        "method": "captum",
        "attributions": attributions,
        "summary": "Tokens found in the reference answer are highlighted as the strongest evidence.",
        "score": score,
    }

"""
Transparent LIME-style explanations for grading decisions.

The output is a compact word-level explanation focused on positive and
negative evidence in the student's answer.
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
    """Return a simple local explanation similar to LIME output."""
    student_tokens = _tokenize(student_answer)
    reference_tokens = set(_tokenize(correct_answer or ""))
    question_tokens = set(_tokenize(question))

    positive = [token for token in student_tokens if token in reference_tokens]
    question_aligned = [token for token in student_tokens if token in question_tokens]
    negative = [token for token in student_tokens if token not in reference_tokens and token not in question_tokens]

    return {
        "method": "lime",
        "attributions": {
            "positive_evidence": positive[:8],
            "question_alignment": question_aligned[:8],
            "extra_or_off_topic": negative[:8],
        },
        "summary": "Words that match the question and reference answer are treated as helpful evidence.",
        "score": score,
    }

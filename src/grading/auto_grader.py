"""
Automated grading engine.

Two entry points:

- `grade_answer(question, student_answer, config)` — used by the test-taking
  flow (src.api.routes.testing). `question` is one of the dicts produced by
  `question_generator.generate_questions` (has "type"/"choices"/"answer").
  MCQ/true-false are graded by exact match (deterministic, free, no LLM
  round-trip needed). Open-ended answers are graded semantically by the LLM
  against the reference answer, with a TF-IDF similarity fallback if no LLM
  backend is configured.

- `grade_response(question, student_answer, rubric, config)` — a more
  generic essay/rubric grading entry point (used by
  src.api.routes.grading), for grading free text against an arbitrary
  rubric dict of {criterion: description}.

Both return a natural-language justification, which the explainability
layer (SHAP/LIME/Captum, still a later phase) is intended to further
ground/verify token-by-token.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.llm import groq_client

logger = logging.getLogger(__name__)


_OPEN_GRADING_SYSTEM_PROMPT = """You are a fair, consistent teaching assistant grading a \
student's short-answer response. You grade on substance and understanding, not phrasing \
or grammar. You give partial credit when the student shows partial understanding."""

_OPEN_GRADING_USER_TEMPLATE = """Question: {question}

Reference/model answer: {reference_answer}

Student's answer: {student_answer}

Grade the student's answer on a scale from 0.0 to 1.0 (fraction of full credit), \
comparing it to the reference answer for substance (not exact wording).

Respond with ONLY a JSON object of this exact shape:
{{
  "score_fraction": <float 0.0-1.0>,
  "justification": "<one or two sentences explaining the score, quoting or referencing \
specific parts of the student's answer>",
  "rubric_breakdown": {{
     "coverage_of_key_points": "<short comment>",
     "accuracy": "<short comment>",
     "clarity": "<short comment>"
  }}
}}"""

_RUBRIC_GRADING_USER_TEMPLATE = """Question: {question}

Rubric (criteria to check for): {rubric}

Student's answer: {student_answer}

Grade the student's answer against each rubric criterion.

Respond with ONLY a JSON object of this exact shape:
{{
  "score_fraction": <float 0.0-1.0, overall score as a fraction of full credit>,
  "justification": "<one or two sentences overall justification>",
  "rubric_breakdown": {{
     "<criterion name>": "<met / partially met / not met - short comment>",
     ...
  }}
}}"""


def _offline_similarity_score(reference_answer: str, student_answer: str) -> float:
    """Cheap offline fallback: TF-IDF cosine similarity between the
    student's answer and the reference answer, used only when no LLM
    backend is configured. Coarser than LLM grading but keeps the app
    functional without an API key."""
    if not student_answer.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([reference_answer, student_answer])
        sim = cosine_similarity(matrix[0], matrix[1])[0][0]
        return float(max(0.0, min(1.0, sim)))
    except ValueError:
        # e.g. both strings reduced to nothing after stopword removal
        return 0.0


def grade_answer(question: dict, student_answer: str, config: dict) -> Dict:
    """Grade a single test-question answer.

    Args:
        question: dict with keys "question", "type" ("mcq"/"true_false"/"open"),
            "choices", "answer" (reference), "explanation"
        student_answer: the raw text the student submitted
        config: parsed config.yaml (uses config['grading']['scale'])

    Returns:
        {
          "is_correct": bool,        # for mcq/true_false; best-effort threshold for open
          "score_fraction": float,   # 0.0-1.0
          "score": float,            # score_fraction * config['grading']['scale']
          "justification": str,
          "rubric_breakdown": dict,
        }
    """
    scale = config.get("grading", {}).get("scale", 10)
    qtype = question.get("type", "mcq")
    reference_answer = question.get("answer", "")

    if qtype in ("mcq", "true_false"):
        is_correct = student_answer.strip() == str(reference_answer).strip()
        score_fraction = 1.0 if is_correct else 0.0
        justification = (
            f"Selected answer matches the correct option ({reference_answer})."
            if is_correct
            else f"Selected answer does not match the correct option ({reference_answer})."
        )
        if question.get("explanation"):
            justification += f" {question['explanation']}"
        return {
            "is_correct": is_correct,
            "score_fraction": score_fraction,
            "score": round(score_fraction * scale, 2),
            "justification": justification,
            "rubric_breakdown": {"exact_match": is_correct},
        }

    # Open-ended: semantic grading
    if groq_client.is_available():
        try:
            prompt = _OPEN_GRADING_USER_TEMPLATE.format(
                question=question.get("question", ""),
                reference_answer=reference_answer,
                student_answer=student_answer,
            )
            result = groq_client.chat_json(_OPEN_GRADING_SYSTEM_PROMPT, prompt, config)
            score_fraction = float(result.get("score_fraction", 0.0))
            score_fraction = max(0.0, min(1.0, score_fraction))
            return {
                "is_correct": score_fraction >= 0.5,
                "score_fraction": score_fraction,
                "score": round(score_fraction * scale, 2),
                "justification": result.get("justification", ""),
                "rubric_breakdown": result.get("rubric_breakdown", {}),
            }
        except Exception as exc:  # noqa: BLE001 - any LLM/parsing failure should degrade, not crash
            logger.warning("LLM grading failed, falling back to TF-IDF similarity: %s", exc)

    score_fraction = _offline_similarity_score(str(reference_answer), student_answer)
    return {
        "is_correct": score_fraction >= 0.5,
        "score_fraction": score_fraction,
        "score": round(score_fraction * scale, 2),
        "justification": (
            f"Offline grading (no LLM backend configured): text-similarity to the "
            f"reference answer was {score_fraction:.2f}. Configure GROQ_API_KEY for "
            f"real semantic grading with a natural-language justification."
        ),
        "rubric_breakdown": {"tfidf_similarity_to_reference": round(score_fraction, 2)},
    }


def grade_response(question: str, student_answer: str, rubric: dict, config: Optional[dict] = None) -> Dict:
    """Generic rubric-based grading of free text (used by /api/grading).

    Returns:
        {
          "score": float,          # out of config['grading']['scale']
          "justification": str,
          "rubric_breakdown": dict
        }
    """
    config = config or {}
    scale = config.get("grading", {}).get("scale", 20)

    if groq_client.is_available():
        try:
            prompt = _RUBRIC_GRADING_USER_TEMPLATE.format(
                question=question, rubric=rubric, student_answer=student_answer
            )
            result = groq_client.chat_json(_OPEN_GRADING_SYSTEM_PROMPT, prompt, config)
            score_fraction = max(0.0, min(1.0, float(result.get("score_fraction", 0.0))))
            return {
                "score": round(score_fraction * scale, 2),
                "justification": result.get("justification", ""),
                "rubric_breakdown": result.get("rubric_breakdown", {}),
            }
        except Exception as exc:  # noqa: BLE001 - any LLM/parsing failure should degrade, not crash
            logger.warning("LLM rubric grading failed, falling back to TF-IDF similarity: %s", exc)

    reference = " ".join(str(v) for v in rubric.values()) if rubric else question
    score_fraction = _offline_similarity_score(reference, student_answer)
    return {
        "score": round(score_fraction * scale, 2),
        "justification": (
            "Offline grading (no LLM backend configured): score derived from "
            "text-similarity to the rubric description. Configure GROQ_API_KEY "
            "for real semantic grading."
        ),
        "rubric_breakdown": {k: "not evaluated (offline mode)" for k in (rubric or {})},
    }

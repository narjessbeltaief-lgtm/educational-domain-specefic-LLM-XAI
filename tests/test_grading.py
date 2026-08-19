"""Unit tests for src.grading.auto_grader."""

from unittest.mock import patch

from src.grading.auto_grader import grade_answer, grade_response

CONFIG = {"grading": {"scale": 20}}


def test_mcq_exact_match_correct():
    question = {"question": "2+2?", "type": "mcq", "choices": ["3", "4"], "answer": "4", "explanation": ""}
    result = grade_answer(question, "4", CONFIG)
    assert result["is_correct"] is True
    assert result["score"] == 20.0


def test_mcq_exact_match_incorrect():
    question = {"question": "2+2?", "type": "mcq", "choices": ["3", "4"], "answer": "4", "explanation": ""}
    result = grade_answer(question, "3", CONFIG)
    assert result["is_correct"] is False
    assert result["score"] == 0.0


def test_true_false_exact_match():
    question = {"question": "Is the sky blue?", "type": "true_false", "choices": ["True", "False"], "answer": "True", "explanation": ""}
    assert grade_answer(question, "True", CONFIG)["is_correct"] is True
    assert grade_answer(question, "False", CONFIG)["is_correct"] is False


def test_open_answer_offline_fallback_uses_similarity():
    """With no LLM configured, open answers should still get a graded score
    via TF-IDF similarity rather than crashing or always returning 0."""
    question = {
        "question": "Explain gravity.",
        "type": "open",
        "choices": None,
        "answer": "Gravity is the force of attraction between masses.",
        "explanation": "",
    }
    with patch("src.grading.auto_grader.groq_client.is_available", return_value=False):
        close = grade_answer(question, "Gravity is the attractive force between masses.", CONFIG)
        far = grade_answer(question, "Bananas are yellow fruit.", CONFIG)

    assert close["score_fraction"] > far["score_fraction"]
    assert "rubric_breakdown" in close


def test_open_answer_llm_path_used_when_available():
    question = {
        "question": "Explain gravity.",
        "type": "open",
        "choices": None,
        "answer": "Gravity is the force of attraction between masses.",
        "explanation": "",
    }
    mock_result = {
        "score_fraction": 0.9,
        "justification": "Correctly describes gravity as an attractive force.",
        "rubric_breakdown": {"accuracy": "good"},
    }
    with patch("src.grading.auto_grader.groq_client.is_available", return_value=True), \
         patch("src.grading.auto_grader.groq_client.chat_json", return_value=mock_result):
        result = grade_answer(question, "It's an attractive force between masses.", CONFIG)

    assert result["score"] == 18.0
    assert result["is_correct"] is True
    assert result["justification"] == mock_result["justification"]


def test_open_answer_llm_failure_falls_back_to_offline():
    question = {
        "question": "Explain gravity.",
        "type": "open",
        "choices": None,
        "answer": "Gravity is the force of attraction between masses.",
        "explanation": "",
    }
    with patch("src.grading.auto_grader.groq_client.is_available", return_value=True), \
         patch("src.grading.auto_grader.groq_client.chat_json", side_effect=RuntimeError("down")):
        result = grade_answer(question, "Gravity pulls things together.", CONFIG)

    assert "offline" in result["justification"].lower() or "Offline" in result["justification"]


def test_grade_response_generic_rubric_grading():
    rubric = {"correctness": "answer must mention Newton's laws"}
    mock_result = {
        "score_fraction": 0.7,
        "justification": "Partially correct.",
        "rubric_breakdown": {"correctness": "partially met"},
    }
    with patch("src.grading.auto_grader.groq_client.is_available", return_value=True), \
         patch("src.grading.auto_grader.groq_client.chat_json", return_value=mock_result):
        result = grade_response("Explain Newton's laws.", "F=ma", rubric, CONFIG)

    assert result["score"] == 14.0
    assert result["rubric_breakdown"] == {"correctness": "partially met"}

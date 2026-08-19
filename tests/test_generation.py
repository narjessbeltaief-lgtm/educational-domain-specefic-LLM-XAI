
"""Unit tests for src.generation.question_generator (TODO: implement)."""

import pytest


@pytest.mark.skip(reason="Not implemented yet")
def test_generate_questions_returns_expected_count():
    pass

from unittest.mock import patch

from src.generation.question_generator import generate_questions

BASE_CONFIG = {
    "llm": {"groq_model": "llama-3.3-70b-versatile", "temperature": 0.3, "max_new_tokens": 1024},
    "rag": {"top_k": 4, "chunk_size": 300, "chunk_overlap": 50},
}


def test_offline_fallback_returns_expected_count():
    """With no LLM backend configured, the offline generator still returns
    the requested number of well-formed questions."""
    with patch("src.llm.groq_client.is_available", return_value=False):
        questions = generate_questions("Newtonian Mechanics", 5, BASE_CONFIG)

    assert len(questions) == 5
    for q in questions:
        assert q["type"] in ("mcq", "true_false", "open")
        assert q["question"]
        assert q["answer"]
        if q["type"] == "open":
            assert q["choices"] is None
        else:
            assert q["answer"] in q["choices"]


def test_offline_fallback_grounds_questions_in_course_text():
    """When real course text is supplied but no LLM is configured, the
    fallback should extract questions from that text rather than emit
    generic 'no course text supplied' placeholders."""
    course_text = (
        "Mitochondria are membrane-bound organelles that generate most of the "
        "chemical energy needed to power the cell's biochemical reactions. "
        "The process of producing energy inside mitochondria is called cellular respiration. "
        "Mitochondria contain their own small circular DNA, separate from nuclear DNA. "
        "Ribosomes are responsible for synthesizing proteins by translating messenger RNA. "
        "The nucleus houses the cell's genetic material organized as chromatin. "
    )
    with patch("src.llm.groq_client.is_available", return_value=False):
        questions = generate_questions(
            "Cell Biology", 4, BASE_CONFIG, course_text=course_text, mcq_ratio=0.5,
        )

    assert len(questions) == 4
    all_text = " ".join(q["question"] + " " + str(q["answer"]) for q in questions)
    assert "placeholder" not in all_text.lower()
    # Every question should reference actual vocabulary from the source text.
    assert any(
        term in all_text
        for term in ("mitochondria", "Mitochondria", "ribosome", "Ribosomes", "nucleus", "respiration")
    )


def test_offline_text_questions_are_not_fill_in_the_blank():
    """Grounded offline questions should read like direct comprehension or
    concept questions, not cloze-style fill-in-the-blank prompts."""
    course_text = (
        "Face detection, face recognition, face marking, and object identification in images all use deep learning. "
        "Convolutional neural networks are especially effective for extracting visual patterns. "
        "Feature extraction helps models detect relevant information from images. "
    )
    with patch("src.llm.groq_client.is_available", return_value=False):
        questions = generate_questions("Computer Vision", 3, BASE_CONFIG, course_text=course_text, mcq_ratio=1.0)

    assert len(questions) == 3
    for q in questions:
        assert not q["question"].lower().startswith("fill in the blank")
        assert "_____" not in q["question"]
        assert len(q["question"]) <= 140
        assert "according to the course material" not in q["question"].lower()
        assert q["question"].strip().endswith("?")


def test_llm_path_parses_fenced_json_and_validates():
    """LLM responses wrapped in ```json fences should parse correctly, and
    malformed entries should be dropped rather than crashing."""
    mock_response = """```json
    [
      {"question": "What is 2+2?", "type": "mcq",
       "choices": ["3", "4", "5", "6"], "answer": "4", "explanation": "Basic arithmetic."},
      {"question": "Malformed entry missing answer", "type": "mcq",
       "choices": ["a", "b"], "answer": "not-in-choices", "explanation": ""},
      {"question": "Explain gravity.", "type": "open", "choices": null,
       "answer": "A force of attraction between masses.", "explanation": ""}
    ]
    ```"""

    with patch("src.llm.groq_client.is_available", return_value=True), \
         patch("src.llm.groq_client._get_client", return_value=object()), \
         patch("src.llm.groq_client.chat_text", return_value=mock_response):
        questions = generate_questions("Physics", 3, BASE_CONFIG)

    # The malformed MCQ (answer not among choices) must be dropped.
    assert len(questions) == 2
    types = {q["type"] for q in questions}
    assert types == {"mcq", "open"}


def test_llm_failure_falls_back_to_offline():
    """If the LLM call raises, generation should degrade gracefully instead
    of propagating the error to the caller."""
    with patch("src.llm.groq_client.is_available", return_value=True), \
         patch("src.llm.groq_client._get_client", return_value=object()), \
         patch("src.llm.groq_client.chat_text", side_effect=RuntimeError("network down")):
        questions = generate_questions("Chemistry", 4, BASE_CONFIG)

    assert len(questions) == 4


def test_rag_grounding_is_used_when_index_available():
    """When use_rag=True and a course_id has an index, the retrieved chunks
    should be injected into the prompt sent to the LLM."""
    from src.rag.indexer import build_index

    text = "Mitochondria are the powerhouse of the cell. " * 30
    build_index("course_rag_test", text, BASE_CONFIG)

    captured_prompts = {}

    def fake_chat_text(system_prompt, user_prompt, config, max_retries=0):
        captured_prompts["user_prompt"] = user_prompt
        return '[{"question": "What are mitochondria?", "type": "open", "choices": null, "answer": "Powerhouse of the cell.", "explanation": ""}]'

    with patch("src.llm.groq_client.is_available", return_value=True), \
         patch("src.llm.groq_client._get_client", return_value=object()), \
         patch("src.llm.groq_client.chat_text", side_effect=fake_chat_text):
        generate_questions(
            "Cell Biology", 1, BASE_CONFIG,
            use_rag=True, course_id="course_rag_test",
        )

    assert "powerhouse of the cell" in captured_prompts["user_prompt"].lower()


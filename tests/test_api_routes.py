"""Integration tests for the FastAPI routes (src.api.main)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_generate_test_offline_and_full_flow():
    with patch("src.generation.question_generator.groq_client.is_available", return_value=False):
        r = client.post(
            "/api/testing/generate",
            json={
                "course_name": "Basic Algebra",
                "course_text": "Algebra is the branch of mathematics dealing with symbols and the rules for manipulating them. " * 5,
                "n_questions": 3,
                "mcq_ratio": 1.0,
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["n_questions"] == 3
    assert len(data["questions"]) == 3
    test_id = data["test_id"]

    # Answer every question as the reference answer -> should be 100%
    for i, q in enumerate(data["questions"], start=1):
        ans_r = client.post(
            "/api/testing/answer",
            json={"test_id": test_id, "student_name": "Bob", "question_num": i, "answer": q["answer"]},
        )
        assert ans_r.status_code == 200
        assert ans_r.json()["is_correct"] is True

    results_r = client.get(f"/api/testing/{test_id}/results/Bob")
    assert results_r.status_code == 200
    results = results_r.json()
    assert results["percentage"] == 100.0

    status_r = client.get(f"/api/testing/status/{test_id}")
    assert status_r.status_code == 200
    assert status_r.json()["progress"] == "3/3"


def test_generate_test_missing_fields_returns_422():
    r = client.post("/api/testing/generate", json={"course_name": "X"})
    assert r.status_code == 422


def test_answer_unknown_test_returns_404():
    r = client.post(
        "/api/testing/answer",
        json={"test_id": "doesnotexist", "student_name": "Bob", "question_num": 1, "answer": "x"},
    )
    assert r.status_code == 404


def test_results_unknown_test_returns_404():
    r = client.get("/api/testing/doesnotexist/results/Bob")
    assert r.status_code == 404


def test_upload_course_rejects_non_pdf():
    r = client.post(
        "/api/testing/upload-course",
        params={"course_name": "X"},
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )
    assert r.status_code == 400


def test_generate_from_pdf_rejects_non_pdf():
    r = client.post(
        "/api/testing/generate-from-pdf",
        data={"course_name": "X", "n_questions": "3", "mcq_ratio": "0.5"},
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )
    assert r.status_code == 400


def test_generate_from_pdf_full_flow():
    from reportlab.pdfgen import canvas
    import io

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    lines = [
        "Newtons first law states that an object in motion stays in motion unless acted on by a force.",
        "Newtons second law defines force as mass multiplied by acceleration.",
        "Newtons third law states that every action has an equal and opposite reaction.",
        "These three laws form the foundation of classical mechanics.",
    ]
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    buf.seek(0)

    with patch("src.generation.question_generator.groq_client.is_available", return_value=False):
        r = client.post(
            "/api/testing/generate-from-pdf",
            data={"course_name": "Newtonian Mechanics", "n_questions": "3", "mcq_ratio": "0.5"},
            files={"file": ("physics.pdf", buf, "application/pdf")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["grounded_in_course_material"] is True
    assert len(data["questions"]) == 3
    # Questions should be grounded in the actual PDF content, not generic
    # placeholder text.
    all_text = " ".join(q["question"] + " " + str(q["answer"]) for q in data["questions"]).lower()
    assert "placeholder" not in all_text


def test_grading_endpoint_uses_mocked_llm():
    mock_result = {
        "score_fraction": 0.6,
        "justification": "Partially correct.",
        "rubric_breakdown": {"correctness": "partially met"},
    }
    with patch("src.grading.auto_grader.groq_client.is_available", return_value=True), \
         patch("src.grading.auto_grader.groq_client.chat_json", return_value=mock_result):
        r = client.post(
            "/api/grading/",
            json={
                "question": "What is F=ma?",
                "student_answer": "Force equals mass times acceleration",
                "rubric": {"correctness": "must state F=ma"},
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["score"] == pytest.approx(0.6 * 20)


def test_generation_endpoint_offline():
    with patch("src.generation.question_generator.groq_client.is_available", return_value=False):
        r = client.post("/api/generation/", json={"topic": "Trigonometry", "n_questions": 2})
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 2
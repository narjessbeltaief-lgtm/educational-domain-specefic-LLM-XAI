"""Endpoints for end-to-end on-demand test generation and grading."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.generation.question_generator import generate_questions
from src.grading.auto_grader import grade_answer
from src.rag.indexer import build_index
from src.utils.config_loader import load_config
from src.utils.pdf_utils import PDFExtractionError, extract_text_from_pdf

router = APIRouter()


class GenerateTestRequest(BaseModel):
    course_name: str
    course_text: str
    n_questions: int = Field(..., ge=1, le=100)
    mcq_ratio: float = Field(0.5, ge=0.0, le=1.0)
    generation_prompt: str | None = None
    allow_open: bool = False


class AnswerRequest(BaseModel):
    test_id: str
    student_name: str
    question_num: int = Field(..., ge=1)
    answer: str


_tests: Dict[str, dict] = {}
_answers: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))


def _assert_pdf(file: UploadFile) -> None:
    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    if content_type != "application/pdf" and not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")


def _generate_test(
    course_name: str,
    course_text: str,
    n_questions: int,
    mcq_ratio: float,
    generation_prompt: str | None = None,
    allow_open: bool = False,
) -> dict:
    cfg = load_config()
    course_id = uuid4().hex[:8]
    indexed_chunks = build_index(course_id, course_text, cfg)

    questions = generate_questions(
        topic=course_name,
        n_questions=n_questions,
        config=cfg,
        course_text=course_text,
        use_rag=indexed_chunks > 0,
        course_id=course_id if indexed_chunks > 0 else None,
        mcq_ratio=mcq_ratio,
        allow_open=allow_open,
        generation_prompt=generation_prompt,
    )

    test_id = uuid4().hex[:8]
    _tests[test_id] = {
        "test_id": test_id,
        "course_id": course_id,
        "course_name": course_name,
        "course_text": course_text,
        "n_questions": len(questions),
        "questions": questions,
    }

    return {
        "test_id": test_id,
        "course_id": course_id,
        "course_name": course_name,
        "n_questions": len(questions),
        "questions": questions,
        "grounded_in_course_material": bool(course_text.strip()),
    }


@router.post("/generate")
def generate_test(request: GenerateTestRequest):
    """Generate an interactive test from pasted course material."""
    try:
        return _generate_test(
            course_name=request.course_name,
            course_text=request.course_text,
            n_questions=request.n_questions,
            mcq_ratio=request.mcq_ratio,
            generation_prompt=request.generation_prompt,
            allow_open=request.allow_open,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not generate test: {exc}")


@router.post("/upload-course")
async def upload_course_pdf(
    course_name: str,
    file: UploadFile = File(...),
):
    """Upload a PDF and extract text, returning a course_id for later use."""
    _assert_pdf(file)
    payload = await file.read()

    try:
        text = extract_text_from_pdf(payload)
    except PDFExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cfg = load_config()
    course_id = uuid4().hex[:8]
    chunks = build_index(course_id, text, cfg)

    return {
        "course_id": course_id,
        "course_name": course_name,
        "indexed_chunks": chunks,
        "chars_extracted": len(text),
    }


@router.post("/generate-from-pdf")
async def generate_test_from_pdf(
    course_name: str | None = Form(None),
    n_questions: int = Form(...),
    mcq_ratio: float = Form(0.5),
    generation_prompt: str | None = Form(None),
    allow_open: bool = Form(False),
    file: UploadFile = File(...),
):
    """Extract PDF course material and generate a test in one request."""
    _assert_pdf(file)
    payload = await file.read()

    try:
        text = extract_text_from_pdf(payload)
    except PDFExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        resolved_course_name = (course_name or "").strip()
        if not resolved_course_name:
            filename = (file.filename or "").strip()
            resolved_course_name = filename.rsplit(".", 1)[0] if "." in filename else filename
        if not resolved_course_name:
            resolved_course_name = "Uploaded PDF Course"

        return _generate_test(
            course_name=resolved_course_name,
            course_text=text,
            n_questions=n_questions,
            mcq_ratio=mcq_ratio,
            generation_prompt=generation_prompt,
            allow_open=allow_open,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not generate test from PDF: {exc}")


@router.post("/answer")
def submit_answer(request: AnswerRequest):
    """Grade one answer and store it in-memory under test_id/student_name."""
    test = _tests.get(request.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Unknown test_id")

    qidx = request.question_num - 1
    questions = test["questions"]
    if qidx < 0 or qidx >= len(questions):
        raise HTTPException(status_code=400, detail="question_num is out of range")

    cfg = load_config()
    question = questions[qidx]
    graded = grade_answer(question=question, student_answer=request.answer, config=cfg)

    feedback = {
        "question_num": request.question_num,
        "student_answer": request.answer,
        "correct_answer": question.get("answer"),
        "is_correct": graded.get("is_correct", False),
        "score": graded.get("score", 0.0),
        "justification": graded.get("justification", ""),
        "rubric_breakdown": graded.get("rubric_breakdown", {}),
    }

    student_entries = _answers[request.test_id][request.student_name]
    existing = next((i for i, a in enumerate(student_entries) if a["question_num"] == request.question_num), None)
    if existing is None:
        student_entries.append(feedback)
    else:
        student_entries[existing] = feedback

    return feedback


@router.get("/{test_id}/results/{student_name}")
def get_results(test_id: str, student_name: str):
    """Return aggregate score and detailed per-question grading feedback."""
    test = _tests.get(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Unknown test_id")

    answers = sorted(
        _answers[test_id].get(student_name, []),
        key=lambda entry: entry["question_num"],
    )

    cfg = load_config()
    scale = cfg.get("grading", {}).get("scale", 10)
    total_score = round(sum(float(a.get("score", 0.0)) for a in answers), 2)
    max_score = round(scale * len(test["questions"]), 2)
    percentage = round((total_score / max_score) * 100, 2) if max_score else 0.0

    return {
        "test_id": test_id,
        "student_name": student_name,
        "course_name": test["course_name"],
        "total_score": total_score,
        "max_score": max_score,
        "percentage": percentage,
        "answers": answers,
    }


@router.get("/status/{test_id}")
def get_test_status(test_id: str):
    """Return completion progress across all students for a test."""
    test = _tests.get(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Unknown test_id")

    answered_count = sum(len(records) for records in _answers[test_id].values())
    total_questions = len(test["questions"])
    remaining = max(total_questions - answered_count, 0)

    return {
        "test_id": test_id,
        "course_name": test["course_name"],
        "progress": f"{min(answered_count, total_questions)}/{total_questions}",
        "remaining": remaining,
    }


@router.get("/{test_id}")
def get_test_status_alias(test_id: str):
    """Backward-compatible alias for fetching test status."""
    return get_test_status(test_id)

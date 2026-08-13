"""Endpoints for on-demand test generation and student answering."""

import uuid
import json
from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.generation.question_generator import generate_questions
from src.utils.config_loader import load_config

router = APIRouter()

# In-memory course/test storage (use database in production)
_courses: Dict[str, dict] = {}
_active_tests: Dict[str, dict] = {}

_config = load_config()


class TestGenerationRequest(BaseModel):
    """Request to generate a new test."""
    course_name: str
    course_text: str
    n_questions: int = 20
    mcq_ratio: float = 0.5


class TestGenerationResponse(BaseModel):
    """Response with generated test."""
    test_id: str
    course_name: str
    n_questions: int
    questions: List[dict]


class StudentAnswerRequest(BaseModel):
    """Student submitting an answer."""
    test_id: str
    student_name: str
    question_num: int
    answer: str


class AnswerFeedback(BaseModel):
    """Feedback for a single answer."""
    question_num: int
    question: str
    correct_answer: str
    student_answer: str
    is_correct: bool
    score: int


class TestResultsResponse(BaseModel):
    """Student's final test results."""
    test_id: str
    student_name: str
    course_name: str
    total_questions: int
    total_score: int
    max_score: int
    percentage: float
    answers: List[AnswerFeedback]


@router.post("/generate", response_model=TestGenerationResponse)
def generate_test(request: TestGenerationRequest):
    """
    Generate a new test with fresh questions from Groq.
    
    Returns a test_id to use for subsequent requests.
    """
    try:
        # Create or update course record
        course_id = str(uuid.uuid4())[:8]
        _courses[course_id] = {
            "course_id": course_id,
            "course_name": request.course_name,
            "course_text": request.course_text,
        }

        # Generate questions grounded in the submitted course material
        questions = generate_questions(
            topic=request.course_name,
            n_questions=request.n_questions,
            config=_config,
            course_text=request.course_text,
            use_rag=False,
            mcq_ratio=request.mcq_ratio,
        )
        
        if not questions:
            raise HTTPException(status_code=502, detail="Failed to generate questions")
        
        # Create test record
        test_id = str(uuid.uuid4())[:8]
        _active_tests[test_id] = {
            "test_id": test_id,
            "course_id": course_id,
            "course_name": request.course_name,
            "questions": questions,
            "students": {},
        }
        
        return TestGenerationResponse(
            test_id=test_id,
            course_name=request.course_name,
            n_questions=len(questions),
            questions=questions,
        )
    
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error generating test: {str(e)}")


@router.post("/answer")
def submit_answer(request: StudentAnswerRequest):
    """Submit a student's answer to a question."""
    try:
        # Get test by test_id
        if request.test_id not in _active_tests:
            raise HTTPException(status_code=404, detail=f"Test {request.test_id} not found")
        
        test_data = _active_tests[request.test_id]
        students = test_data.setdefault("students", {})
        student_answers = students.setdefault(request.student_name, {})
        
        questions = test_data["questions"]
        if request.question_num < 1 or request.question_num > len(questions):
            raise HTTPException(status_code=400, detail="Invalid question number")
        
        question = questions[request.question_num - 1]
        is_correct = request.answer == question["answer"]
        score = 10 if is_correct else 0
        
        # Store answer per student
        student_answers[request.question_num] = {
            "answer": request.answer,
            "is_correct": is_correct,
            "score": score,
        }
        
        return {
            "question_num": request.question_num,
            "correct_answer": question["answer"],
            "student_answer": request.answer,
            "is_correct": is_correct,
            "score": score,
            "feedback": "Correct!" if is_correct else "Incorrect. Try again!",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}/results/{student_name}", response_model=TestResultsResponse)
def get_test_results(test_id: str, student_name: str):
    """Get student's final test results."""
    try:
        if test_id not in _active_tests:
            raise HTTPException(status_code=404, detail="Test not found")
        
        test_data = _active_tests[test_id]
        questions = test_data["questions"]
        students = test_data.setdefault("students", {})
        student_answers = students.get(student_name, {})
        
        # Calculate totals
        total_score = sum(ans["score"] for ans in student_answers.values())
        max_score = len(questions) * 10
        percentage = round((total_score / max_score) * 100, 2) if max_score > 0 else 0
        
        # Build answer details
        answers = []
        for q_num, question in enumerate(questions, 1):
            student_ans = student_answers.get(q_num, {})
            answers.append(
                AnswerFeedback(
                    question_num=q_num,
                    question=question["question"],
                    correct_answer=question["answer"],
                    student_answer=student_ans.get("answer", "Not answered"),
                    is_correct=student_ans.get("is_correct", False),
                    score=student_ans.get("score", 0),
                )
            )
        
        return TestResultsResponse(
            test_id=test_id,
            student_name=student_name,
            course_name=test_data.get("course_name", test_data.get("topic", "")),
            total_questions=len(questions),
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            answers=answers,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{test_id}")
def get_test_status(test_id: str):
    """Get test information and current progress."""
    if test_id not in _active_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    test_data = _active_tests[test_id]
    students = test_data.setdefault("students", {})
    answered = sum(len(ans) for ans in students.values())
    total = len(test_data["questions"])
    
    return {
        "test_id": test_id,
        "course_name": test_data.get("course_name", test_data.get("topic", "")),
        "students": list(students.keys()),
        "total_students": len(students),
        "total_questions": total,
        "answered": answered,
        "remaining": total - answered,
        "progress": f"{answered}/{total}",
    }

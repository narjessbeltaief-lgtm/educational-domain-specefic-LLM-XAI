"""Endpoints for the automated grading engine."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import GradeRequest, GradeResponse
from src.grading.auto_grader import grade_response
from src.utils.config_loader import load_config

router = APIRouter()


@router.post("/", response_model=GradeResponse)
def grade_endpoint(request: GradeRequest):
    """Grade a student's response against the given rubric."""
    try:
        config = load_config()
        result = grade_response(
            question=request.question,
            student_answer=request.student_answer,
            rubric=request.rubric,
            config=config,
        )
        return GradeResponse(**result)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error grading response: {str(e)}")

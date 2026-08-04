"""Endpoints for the automated grading engine."""

from fastapi import APIRouter

from src.api.schemas import GradeRequest, GradeResponse

router = APIRouter()


@router.post("/", response_model=GradeResponse)
def grade_endpoint(request: GradeRequest):
    """Grade a student's response against the given rubric."""
    raise NotImplementedError("TODO: call src.grading.auto_grader.grade_response")

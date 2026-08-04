"""Endpoints for the question generation engine."""

from fastapi import APIRouter

from src.api.schemas import GenerateQuestionsRequest, GenerateQuestionsResponse

router = APIRouter()


@router.post("/", response_model=GenerateQuestionsResponse)
def generate_questions_endpoint(request: GenerateQuestionsRequest):
    """Generate `n_questions` pedagogically relevant questions for `topic`."""
    raise NotImplementedError("TODO: call src.generation.question_generator.generate_questions")

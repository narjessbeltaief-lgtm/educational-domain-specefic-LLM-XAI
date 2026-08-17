"""Endpoints for the question generation engine."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import GenerateQuestionsRequest, GenerateQuestionsResponse
from src.generation.question_generator import generate_questions
from src.utils.config_loader import load_config

router = APIRouter()


@router.post("/", response_model=GenerateQuestionsResponse)
def generate_questions_endpoint(request: GenerateQuestionsRequest):
    """Generate `n_questions` pedagogically relevant questions for `topic`."""
    try:
        cfg = load_config()
        questions = generate_questions(
            topic=request.topic, n_questions=request.n_questions, config=cfg
        )
        return GenerateQuestionsResponse(questions=questions)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

"""Pydantic request/response models shared across API routes."""

from typing import List, Optional
from pydantic import BaseModel


class GenerateQuestionsRequest(BaseModel):
    topic: str
    n_questions: int = 5


class Question(BaseModel):
    question: str
    type: str
    choices: Optional[List[str]] = None
    answer: Optional[str] = None


class GenerateQuestionsResponse(BaseModel):
    questions: List[Question]


class GradeRequest(BaseModel):
    question: str
    student_answer: str
    rubric: dict


class GradeResponse(BaseModel):
    score: float
    justification: str
    rubric_breakdown: dict


class ExplainRequest(BaseModel):
    text: str
    method: str = "shap"  # shap | lime | captum


class ExplainResponse(BaseModel):
    method: str
    attributions: dict

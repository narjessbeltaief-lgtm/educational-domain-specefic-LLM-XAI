"""Endpoints exposing transparent XAI explanations for grading decisions."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import ExplainRequest, ExplainResponse
from src.explainability.captum_explainer import explain as captum_explain
from src.explainability.lime_explainer import explain as lime_explain
from src.explainability.shap_explainer import explain as shap_explain

router = APIRouter()


@router.post("/", response_model=ExplainResponse)
def explain_endpoint(request: ExplainRequest):
    """Return a transparent explanation for a grading decision."""
    method = request.method.lower().strip()
    if method == "shap":
        result = shap_explain(request.question, request.student_answer, request.correct_answer, request.score)
    elif method == "lime":
        result = lime_explain(request.question, request.student_answer, request.correct_answer, request.score)
    elif method == "captum":
        result = captum_explain(request.question, request.student_answer, request.correct_answer, request.score)
    else:
        raise HTTPException(status_code=400, detail="method must be shap, lime, or captum")

    return ExplainResponse(method=result["method"], attributions=result["attributions"])

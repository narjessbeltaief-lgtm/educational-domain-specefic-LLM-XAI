"""Endpoints exposing SHAP / LIME / Captum explanations for a grading decision."""

from fastapi import APIRouter

from src.api.schemas import ExplainRequest, ExplainResponse

router = APIRouter()


@router.post("/", response_model=ExplainResponse)
def explain_endpoint(request: ExplainRequest):
    """Return an explanation for `request.text` using `request.method`."""
    raise NotImplementedError(
        "TODO: dispatch to src.explainability.{shap,lime,captum}_explainer based on method"
    )

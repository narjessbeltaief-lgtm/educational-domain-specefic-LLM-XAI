"""Unit tests for src.explainability.* modules."""

from src.explainability.captum_explainer import explain as captum_explain
from src.explainability.lime_explainer import explain as lime_explain
from src.explainability.shap_explainer import explain as shap_explain


QUESTION = "What is the past participle of take?"
STUDENT = "The answer is taken because take changes to taken."
REFERENCE = "taken"


def test_shap_explainer_returns_attributions():
    result = shap_explain(QUESTION, STUDENT, REFERENCE, 10)
    assert result["method"] == "shap"
    assert result["attributions"]


def test_lime_explainer_returns_attributions():
    result = lime_explain(QUESTION, STUDENT, REFERENCE, 10)
    assert result["method"] == "lime"
    assert "positive_evidence" in result["attributions"]


def test_captum_explainer_returns_attributions():
    result = captum_explain(QUESTION, STUDENT, REFERENCE, 10)
    assert result["method"] == "captum"
    assert result["attributions"]

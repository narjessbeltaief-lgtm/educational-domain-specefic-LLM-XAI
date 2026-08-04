"""
SHAP-based explanations for grading decisions: attributes the grading
score/output to specific tokens/phrases in the student's response.
"""


def explain(text: str, model, tokenizer, config: dict):
    """Return SHAP values highlighting influential tokens in `text`."""
    raise NotImplementedError

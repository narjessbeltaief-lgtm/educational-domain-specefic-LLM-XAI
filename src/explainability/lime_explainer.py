"""
LIME-based local explanations, complementary to SHAP, for grading
decisions on student responses.
"""


def explain(text: str, model, tokenizer, config: dict):
    """Return a LIME explanation object for the grading model's decision on `text`."""
    raise NotImplementedError

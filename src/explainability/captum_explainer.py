"""
Captum-based (integrated gradients / layer attribution) explanations,
operating directly on the PyTorch model internals for deeper,
gradient-based attribution of the grading decision.
"""


def explain(text: str, model, tokenizer, config: dict):
    """Return Captum attribution scores for `text` w.r.t. the grading output."""
    raise NotImplementedError

"""
Automated grading engine.

Evaluates a student's response against a question + rubric, producing
a score and a natural-language justification. The justification is
later grounded/verified by the explainability layer (SHAP/LIME/Captum).
"""

from typing import Dict


def grade_response(question: str, student_answer: str, rubric: dict, config: dict) -> Dict:
    """
    Returns:
        {
          "score": float,          # out of config['grading']['scale']
          "justification": str,   # natural-language explanation
          "rubric_breakdown": dict
        }
    """
    raise NotImplementedError

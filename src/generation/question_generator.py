"""
Intelligent question generation engine.

Given a topic/learning objective (optionally grounded via RAG retrieval
of course material), generates pedagogically relevant assessment
questions (MCQ, open-ended, etc.) using the fine-tuned LLM.
"""

from typing import List


def generate_questions(topic: str, n_questions: int, config: dict) -> List[dict]:
    """
    Args:
        topic: learning objective / chapter / concept to assess
        n_questions: number of questions to generate
        config: parsed config.yaml

    Returns:
        List of question dicts, e.g.
        {"question": str, "type": "mcq"|"open", "choices": [...], "answer": str}
    """
    raise NotImplementedError

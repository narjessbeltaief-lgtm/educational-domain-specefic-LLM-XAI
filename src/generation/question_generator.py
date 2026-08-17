"""
Intelligent question generation engine.

Given a topic/learning objective (optionally grounded via RAG retrieval
of course material), generates pedagogically relevant assessment
questions (MCQ, open-ended, etc.) using the fine-tuned LLM.
"""

from typing import List, Optional
import random


def generate_questions(
    topic: str,
    n_questions: int,
    config: dict,
    course_text: Optional[str] = None,
    use_rag: bool = False,
    mcq_ratio: float = 0.5,
) -> List[dict]:
    """Generate simple pedagogical questions for a given topic.

    This is a lightweight, deterministic (per-runtime) generator used for
    testing and demo purposes. It returns a list of question dictionaries
    that other parts of the system expect: keys `question`, `type`,
    optional `choices`, and `answer`.

    Parameters:
        topic: topic or learning objective
        n_questions: how many questions to produce
        config: configuration dict (not required by this simple impl)
        course_text: optional grounding text (ignored by default)
        use_rag: whether RAG should be used (not implemented here)
        mcq_ratio: fraction of questions that should be MCQs

    Returns:
        List[dict]: question objects
    """

    random.seed(topic)  # make generation stable per-topic within a run
    questions: List[dict] = []

    # small helper to create a plausible MCQ
    def make_mcq(i: int) -> dict:
        correct = f"Key concept about {topic} (answer {i + 1})"
        # create 3 distractors + correct, shuffled
        distractors = [
            f"Common misconception {j} for {topic}" for j in range(1, 4)
        ]
        choices = distractors + [correct]
        random.shuffle(choices)
        return {
            "question": f"({i+1}) Which statement best describes {topic}?",
            "type": "mcq",
            "choices": choices,
            "answer": correct,
        }

    def make_yes_no(i: int) -> dict:
        ans = "Yes" if random.random() > 0.5 else "No"
        return {
            "question": f"({i+1}) Is the following statement true about {topic}?",
            "type": "yes_no",
            "choices": ["Yes", "No"],
            "answer": ans,
        }

    def make_open(i: int) -> dict:
        return {
            "question": f"({i+1}) Explain the main idea behind {topic} in a few sentences.",
            "type": "open",
            "choices": None,
            "answer": f"A concise explanation of {topic} (model answer {i + 1})",
        }

    for i in range(n_questions):
        r = random.random()
        if r < mcq_ratio:
            q = make_mcq(i)
        else:
            # choose between yes_no and open for diversity
            if random.random() < 0.7:
                q = make_yes_no(i)
            else:
                q = make_open(i)
        questions.append(q)

    return questions

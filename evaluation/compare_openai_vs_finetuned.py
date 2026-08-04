"""
Comparative evaluation: baseline LLM (e.g. OpenAI GPT) vs. the
domain-specific fine-tuned LLM, on question generation quality and
grading accuracy/consistency.

Produces a report saved to evaluation/results/.
"""


def run_comparison(config: dict) -> None:
    """
    1. Generate questions & grade sample responses with the baseline model
    2. Generate questions & grade the same samples with the fine-tuned model
    3. Score both on relevant metrics (e.g. relevance, grading agreement
       with human graders, hallucination rate)
    4. Save comparison report (CSV/JSON + summary) to evaluation/results/
    """
    raise NotImplementedError


if __name__ == "__main__":
    raise NotImplementedError("Wire up config loading + run_comparison() call")

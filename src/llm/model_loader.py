"""
Loads the base or fine-tuned LLM + tokenizer used across the pipeline
(question generation, grading, explainability).

Responsibilities:
- Load base model from Hugging Face Hub (or local cache)
- Optionally attach a LoRA/PEFT adapter (fine-tuned weights)
- Expose a single `get_model_and_tokenizer()` entrypoint used by every
  other module (generation, grading, explainability) so the model is
  loaded once and reused.
"""

from typing import Tuple


def get_model_and_tokenizer(config: dict) -> Tuple[object, object]:
    """
    Load the model/tokenizer described in `config['llm']`.

    Args:
        config: parsed contents of config/config.yaml

    Returns:
        (model, tokenizer)
    """
    raise NotImplementedError("TODO: load base model + optional LoRA adapter")

"""
Fine-tunes the base LLM on a domain-specific educational corpus using
PEFT/LoRA (parameter-efficient fine-tuning).

Expected input: data/processed/train.jsonl (instruction/response pairs
built from the target educational domain, e.g. question-answer-rubric
triples).

Output: LoRA adapter weights saved to config['llm']['fine_tuned_path'].
"""


def build_lora_config(config: dict):
    """Build a peft.LoraConfig from config['peft']."""
    raise NotImplementedError


def train(config: dict) -> None:
    """
    Run the fine-tuning loop:
    1. Load base model + tokenizer
    2. Wrap with LoRA adapter (peft.get_peft_model)
    3. Load & tokenize training dataset
    4. Train with Hugging Face Trainer / accelerate
    5. Save adapter weights
    """
    raise NotImplementedError


if __name__ == "__main__":
    # Entrypoint: python -m src.llm.fine_tuning
    raise NotImplementedError("Wire up config loading + train() call")

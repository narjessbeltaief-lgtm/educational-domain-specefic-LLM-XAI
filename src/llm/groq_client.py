"""
Thin wrapper around the Groq chat-completions API.

This is the single place that talks to the LLM provider. Every other module
(question generation, grading) should go through `chat_json()` /
`chat_text()` instead of importing the `groq` SDK directly, so that:

  - the model name / temperature / API key all come from config in one place
  - JSON parsing + retry-on-malformed-output logic is not duplicated
  - it's easy to swap providers later (OpenAI, local model, etc.) by editing
    this one file

Behaviour when no API key is configured:
  `is_available()` returns False and callers are expected to fall back to a
  deterministic offline generator (see question_generator.py / auto_grader.py)
  so the rest of the app keeps working in a demo/offline environment.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:  # pragma: no cover - groq is a required dependency, but degrade gracefully
    Groq = None


class GroqClientError(RuntimeError):
    """Raised when the Groq API call fails after retries."""


_client_cache: Optional["Groq"] = None


def _get_client() -> Optional["Groq"]:
    """Lazily build and cache a Groq client from GROQ_API_KEY."""
    global _client_cache
    if _client_cache is not None:
        return _client_cache

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or Groq is None:
        return None

    _client_cache = Groq(api_key=api_key)
    return _client_cache


def is_available() -> bool:
    """Whether a real LLM backend is configured and usable."""
    return _get_client() is not None


def _extract_json(raw: str) -> str:
    """Best-effort extraction of a JSON array/object from a model response.

    Models sometimes wrap JSON in ```json fences or add a short preamble
    despite being asked for JSON only. This strips that noise.
    """
    text = raw.strip()
    # Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # If there's leading/trailing prose, grab the outermost [...] or {...}
    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
    return text


def chat_text(
    system_prompt: str,
    user_prompt: str,
    config: dict,
    max_retries: int = 2,
) -> str:
    """Call the LLM and return the raw text response.

    Raises GroqClientError if the client isn't configured or the call fails
    after `max_retries` attempts.
    """
    client = _get_client()
    if client is None:
        raise GroqClientError(
            "GROQ_API_KEY not set (or `groq` package unavailable); "
            "no LLM backend is configured."
        )

    llm_cfg = config.get("llm", {})
    model = llm_cfg.get("groq_model", "llama-3.3-70b-versatile")
    temperature = llm_cfg.get("temperature", 0.3)
    max_tokens = llm_cfg.get("max_new_tokens", 1024)

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:  # noqa: BLE001 - surface any SDK/network error
            last_error = exc
            logger.warning("Groq call failed (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)

    raise GroqClientError(f"Groq API call failed after {max_retries + 1} attempts: {last_error}")


def chat_json(
    system_prompt: str,
    user_prompt: str,
    config: dict,
    max_retries: int = 2,
) -> dict | list:
    """Call the LLM expecting a JSON response and parse it.

    Appends a strict "respond with JSON only" instruction to the system
    prompt and retries once with an explicit correction if parsing fails.
    """
    strict_system = (
        system_prompt
        + "\n\nCRITICAL: Respond with ONLY valid JSON. No prose, no markdown "
        "code fences, no explanation before or after the JSON."
    )

    last_error: Optional[Exception] = None
    prompt = user_prompt
    for attempt in range(max_retries + 1):
        raw = chat_text(strict_system, prompt, config, max_retries=0)
        try:
            return json.loads(_extract_json(raw))
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("Failed to parse JSON from LLM (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)
            prompt = (
                user_prompt
                + f"\n\nYour previous response could not be parsed as JSON "
                f"(error: {exc}). Respond again with ONLY valid JSON, "
                f"no other text."
            )

    raise GroqClientError(f"Could not get valid JSON from Groq after {max_retries + 1} attempts: {last_error}")

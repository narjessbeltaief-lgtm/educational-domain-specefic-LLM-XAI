"""
Retrieves the most relevant course-material chunks for a given query,
used by the generation and grading modules to ground the LLM in actual
uploaded content instead of relying purely on its parametric knowledge.
"""

from __future__ import annotations

import logging
from typing import List

from sklearn.metrics.pairwise import cosine_similarity

from src.rag.indexer import load_index

logger = logging.getLogger(__name__)


def retrieve(course_id: str, query: str, config: dict, top_k: int | None = None) -> List[str]:
    """Return the top_k chunks most relevant to `query` for a given course.

    Returns an empty list if the course has no built index (caller should
    fall back to non-RAG generation), which keeps this a soft dependency
    rather than a hard requirement.
    """
    index = load_index(course_id)
    if index is None or not index.chunks:
        return []

    rag_cfg = config.get("rag", {})
    k = top_k or rag_cfg.get("top_k", 4)
    k = min(k, len(index.chunks))

    query_vec = index.vectorizer.transform([query])
    sims = cosine_similarity(query_vec, index.matrix)[0]

    ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
    top_indices = [i for i in ranked[:k] if sims[i] > 0]

    if not top_indices:
        # No lexical overlap at all; fall back to the first k chunks so the
        # generator still has *some* grounding rather than none.
        top_indices = list(range(k))

    return [index.chunks[i] for i in top_indices]


def format_context(chunks: List[str], max_chars: int = 6000) -> str:
    """Join retrieved chunks into a single context block for prompting,
    truncated to keep prompts a reasonable size."""
    context = "\n\n---\n\n".join(chunks)
    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[...truncated...]"
    return context

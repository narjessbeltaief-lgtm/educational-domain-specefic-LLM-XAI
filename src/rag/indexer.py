"""
Builds and persists a retrieval index over course material, used to ground
question generation and grading in the actual uploaded content (RAG).

Implementation note
--------------------
The project's config lists FAISS/ChromaDB + sentence-transformers as the
target retrieval stack. Those require downloading an embedding model from
the Hugging Face Hub, which needs network-dependent setup. Since this
deployment target has no GPU and should work offline/out of the box, this
module defaults to a TF-IDF + cosine-similarity index (scikit-learn), which
is lightweight, dependency-light, and needs no model download. It is
swapped in behind the same `build_index` / `retrieve` interface, so a
FAISS/embedding-based backend can be dropped in later (see `rag.backend`
in config.yaml) without touching callers.
"""

from __future__ import annotations

import logging
import os
import pickle
import re
from dataclasses import dataclass, field
from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

_VECTORSTORE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "vectorstore"
)


@dataclass
class CourseIndex:
    course_id: str
    chunks: List[str] = field(default_factory=list)
    vectorizer: Optional[TfidfVectorizer] = None
    matrix: object = None  # scipy sparse matrix, one row per chunk


# In-memory cache so repeated queries in the same process don't hit disk.
_index_cache: dict = {}


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
    """Split text into overlapping word-based chunks.

    chunk_size / chunk_overlap are measured in words (not tokens) to avoid
    a tokenizer dependency; this is a reasonable approximation for chunking
    prose course material.
    """
    words = re.sub(r"\s+", " ", text).strip().split(" ")
    words = [w for w in words if w]
    if not words:
        return []

    chunks = []
    step = max(chunk_size - chunk_overlap, 1)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
    return chunks


def _index_path(course_id: str) -> str:
    return os.path.join(_VECTORSTORE_DIR, f"{course_id}.pkl")


def build_index(course_id: str, text: str, config: dict) -> int:
    """Chunk `text` and build a TF-IDF index for it, persisted to disk.

    Args:
        course_id: unique identifier for the course/document
        text: raw course material (from a pasted topic description, PDF, etc.)
        config: parsed config.yaml (uses config['rag'])

    Returns:
        Number of chunks indexed. Returns 0 if the text was too short/empty
        to index (callers should fall back to non-RAG generation in that case).
    """
    rag_cfg = config.get("rag", {})
    chunk_size = rag_cfg.get("chunk_size", 512)
    chunk_overlap = rag_cfg.get("chunk_overlap", 64)

    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        logger.info("No chunks produced for course_id=%s; skipping index build.", course_id)
        return 0

    vectorizer = TfidfVectorizer(stop_words="english", max_features=20000)
    matrix = vectorizer.fit_transform(chunks)

    index = CourseIndex(course_id=course_id, chunks=chunks, vectorizer=vectorizer, matrix=matrix)
    _index_cache[course_id] = index

    try:
        os.makedirs(_VECTORSTORE_DIR, exist_ok=True)
        with open(_index_path(course_id), "wb") as f:
            pickle.dump(index, f)
    except OSError as exc:
        # Persistence is best-effort; in-memory cache still works for this run.
        logger.warning("Could not persist vector index for course_id=%s: %s", course_id, exc)

    logger.info("Indexed %d chunks for course_id=%s", len(chunks), course_id)
    return len(chunks)


def load_index(course_id: str):
    """Load a course's index from the in-memory cache, or disk if not cached."""
    if course_id in _index_cache:
        return _index_cache[course_id]

    path = _index_path(course_id)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "rb") as f:
            index = pickle.load(f)
        _index_cache[course_id] = index
        return index
    except (OSError, pickle.PickleError) as exc:
        logger.warning("Could not load persisted vector index for course_id=%s: %s", course_id, exc)
        return None


def has_index(course_id: str) -> bool:
    return load_index(course_id) is not None

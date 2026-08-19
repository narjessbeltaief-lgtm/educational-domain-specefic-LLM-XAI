"""Unit tests for src.rag.indexer / src.rag.retriever."""

from src.rag.indexer import build_index, chunk_text, has_index
from src.rag.retriever import retrieve

CONFIG = {"rag": {"chunk_size": 20, "chunk_overlap": 5, "top_k": 2}}


def test_chunk_text_respects_overlap_and_covers_all_words():
    text = " ".join(f"word{i}" for i in range(50))
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    assert len(chunks) > 1
    # Every word should show up in at least one chunk.
    all_chunked_words = set(" ".join(chunks).split())
    assert all_chunked_words == set(text.split())


def test_chunk_text_empty_input():
    assert chunk_text("", chunk_size=10, chunk_overlap=2) == []
    assert chunk_text("   ", chunk_size=10, chunk_overlap=2) == []


def test_build_index_and_retrieve_relevant_chunk():
    text = (
        "Photosynthesis converts light energy into chemical energy in plants. " * 15
        + "Cellular respiration breaks down glucose to release usable energy in cells. " * 15
    )
    n = build_index("test_course_rag", text, CONFIG)
    assert n > 0
    assert has_index("test_course_rag")

    results = retrieve("test_course_rag", "cellular respiration glucose breakdown", CONFIG)
    assert len(results) > 0
    assert any("respiration" in c.lower() for c in results)


def test_retrieve_missing_course_returns_empty():
    assert retrieve("course_that_does_not_exist", "anything", CONFIG) == []

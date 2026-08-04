"""
Builds and persists the vector index (FAISS or ChromaDB) over the
educational course material, used to ground question generation and
grading in actual course content (RAG).
"""


def build_index(source_dir: str, config: dict) -> None:
    """
    1. Load raw documents from `source_dir` (data/raw/)
    2. Chunk text (config['rag']['chunk_size'] / chunk_overlap)
    3. Embed chunks with config['rag']['embedding_model']
    4. Persist to config['rag']['backend'] at data/vectorstore/
    """
    raise NotImplementedError

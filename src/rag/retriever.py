"""
LangChain-based retriever used by the generation and grading modules
to fetch the most relevant course-material chunks for a given query.
"""


def get_retriever(config: dict):
    """
    Load the persisted vector store (FAISS/ChromaDB) and wrap it as a
    LangChain retriever, configured with config['rag']['top_k'].
    """
    raise NotImplementedError

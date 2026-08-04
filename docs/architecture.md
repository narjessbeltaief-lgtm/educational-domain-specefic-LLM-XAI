# Architecture

> TODO: fill in as the design solidifies.

## High-level flow

```
[Course material] --(indexer.py)--> [Vector store: FAISS/ChromaDB]
                                            |
                                     (retriever.py, LangChain)
                                            |
[Student / Teacher] --REST API--> [FastAPI] --> [question_generator.py] --> Questions
                                            \--> [auto_grader.py] --------> Score + justification
                                                        |
                                            [explainability/*.py: SHAP/LIME/Captum]
                                                        |
                                            Transparent explanation returned to client
                                                        |
                                        [Spring Boot platform] (consumer of REST API)
```

## Components

- **LLM layer** (`src/llm/`): base model + LoRA fine-tuned adapter
- **RAG layer** (`src/rag/`): grounds generation/grading in real course content
- **Generation** (`src/generation/`): produces assessment questions
- **Grading** (`src/grading/`): scores student responses against rubrics
- **Explainability** (`src/explainability/`): SHAP/LIME/Captum explanations
- **API** (`src/api/`): REST layer consumed by the Spring Boot platform

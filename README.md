# XAI Framework for Intelligent Educational Assessment

**Sujet #16** — Development of an Explainable AI Framework for Intelligent
Educational Assessment Using Large Language Models

Encadré par : Mme. Fatma Sbiaa
Domaine : XAI, LLMs

## Objective

Design and implement an Explainable AI (XAI) framework for educational
assessment by developing and evaluating a domain-specific Large Language
Model capable of:

1. Generating pedagogically relevant assessment questions
2. Automatically evaluating (grading) student responses
3. Providing transparent, human-readable explanations of its decisions

## Current Status (updated)

| Deliverable | Status |
|---|---|
| Question generation (LLM + RAG-grounded) | ✅ Implemented — `src/generation/question_generator.py`, real Groq LLM call with offline fallback |
| RAG pipeline (retrieval over uploaded course material) | ✅ Implemented — `src/rag/indexer.py` / `retriever.py` (TF-IDF, see note below) |
| PDF course upload | ✅ Implemented — `POST /api/testing/upload-course` |
| Automated grading engine | ✅ Implemented — exact-match for MCQ/true-false, LLM semantic grading + justification for open answers, offline TF-IDF fallback — `src/grading/auto_grader.py` |
| REST API (FastAPI) | ✅ Implemented and wired up — `src/api/main.py` (previously the `testing` router wasn't even registered; fixed) |
| Explainable AI framework (SHAP/LIME/Captum) | ⬜ Not implemented — `src/explainability/*.py` are stubs |
| Persistence (DB, history, leaderboard) | ⬜ Not implemented — everything is in-memory, resets on restart |
| Educational domain-specific **fine-tuned** LLM (PEFT/LoRA) | ⬜ Not implemented — `src/llm/fine_tuning.py` is a stub; requires GPU access |
| Adaptive difficulty / personalized feedback | ⬜ Not implemented |
| Comparative evaluation report (baseline vs fine-tuned) | ⬜ Not implemented (no fine-tuned model to compare yet) |

**Note on the RAG backend:** the config/stack originally targeted
FAISS/ChromaDB + `sentence-transformers` embeddings. That requires
downloading an embedding model from the Hugging Face Hub. Since this
deployment target has no GPU and should run fully offline/CPU-only out of
the box, the RAG layer defaults to a TF-IDF + cosine-similarity index
(scikit-learn) instead — same `build_index()` / `retrieve()` interface, so
swapping in FAISS/embeddings later is a drop-in change (`config/config.yaml`
→ `rag.backend`).

**Note on the LLM backend:** with no GPU available, generation and grading
run against the **Groq API** (`llama-3.3-70b-versatile` by default) rather
than a locally-hosted fine-tuned model. Set `GROQ_API_KEY` in `.env` to
enable it — see `.env.example`. Without a key, the app falls back to a
deterministic offline generator/grader so the API and UI stay usable for
local demos and tests.

## Expected Deliverables

- [ ] Educational domain-specific fine-tuned LLM
- [x] Explainable AI framework (SHAP / LIME / Captum) — *next phase*
- [x] Intelligent question generation engine
- [x] Automated grading engine
- [x] REST API services for platform integration (Spring Boot)
- [ ] Comparative evaluation report (OpenAI/base LLM vs. fine-tuned LLM)
- [ ] Technical documentation

## Project Structure

```
xai-edu-assessment/
├── config/                  # YAML/env configuration
├── data/
│   ├── raw/                 # Raw educational corpora / datasets
│   ├── processed/           # Cleaned & tokenized data
│   └── vectorstore/         # FAISS / ChromaDB persisted indexes
├── notebooks/                # Exploration & prototyping notebooks
├── src/
│   ├── llm/                  # Model loading, PEFT/LoRA fine-tuning
│   ├── rag/                  # LangChain retrieval pipeline (FAISS/ChromaDB)
│   ├── generation/           # Question generation engine
│   ├── grading/              # Automated grading engine
│   ├── explainability/       # SHAP, LIME, Captum explainers
│   ├── api/                  # REST API (FastAPI) exposed to Spring Boot
│   └── utils/                # Shared helpers (logging, config loading)
├── tests/                    # Unit tests mirroring src/
├── evaluation/                # OpenAI vs fine-tuned LLM comparison scripts
│   └── results/
├── docs/                      # Architecture & technical documentation
└── spring-integration/        # Notes/contracts for Spring Boot integration
```

## Tech Stack

- **Modeling**: Python, PyTorch, Hugging Face Transformers, PEFT/LoRA
- **Retrieval**: LangChain, FAISS or ChromaDB (RAG)
- **Explainability**: SHAP, LIME, Captum
- **Serving**: REST APIs (FastAPI), Spring Boot integration on the client side

## Getting Started

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template and fill in your Groq API key
#    (get a free key at https://console.groq.com/keys)
cp .env.example .env

# 4. Run the API locally
uvicorn src.api.main:app --reload   # http://localhost:8000, docs at /docs

# 5. (optional) Run the demo web UI in a second terminal
python serve_ui.py                  # http://localhost:8080
```

Without a `GROQ_API_KEY` set, the app still runs — question generation and
grading fall back to a deterministic offline mode so you can exercise the
full flow without an API key.

Run the test suite with `pytest tests/ -v`.
## Roadmap (suggested phases)

1. **Phase 1 — Data & baseline**: collect domain corpus, set up baseline LLM
   (e.g. via OpenAI API) for question generation & grading.
2. **Phase 2 — Fine-tuning**: fine-tune an open-source LLM with PEFT/LoRA on
   the educational domain corpus.
3. **Phase 3 — RAG pipeline**: build retrieval layer (FAISS/ChromaDB +
   LangChain) to ground generation/grading in course material.
4. **Phase 4 — Explainability**: integrate SHAP/LIME/Captum to explain
   grading decisions and generated question rationale.
5. **Phase 5 — API & integration**: expose REST endpoints, integrate with
   Spring Boot platform.
6. **Phase 6 — Evaluation**: comparative report (baseline vs fine-tuned),
   write technical documentation.

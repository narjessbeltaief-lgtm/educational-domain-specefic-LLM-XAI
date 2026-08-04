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

## Expected Deliverables

- [ ] Educational domain-specific fine-tuned LLM
- [ ] Explainable AI framework (SHAP / LIME / Captum)
- [ ] Intelligent question generation engine
- [ ] Automated grading engine
- [ ] REST API services for platform integration (Spring Boot)
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

# 3. Copy environment template and fill in secrets
cp .env.example .env

# 4. Run the API locally
uvicorn src.api.main:app --reload
```

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

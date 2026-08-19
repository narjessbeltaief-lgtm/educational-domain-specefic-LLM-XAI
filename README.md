# XAI Educational Assessment

This project creates short educational tests from course material, grades the
answers, and shows simple feedback. It also uses retrieval and LLM support to
keep the questions grounded in the lesson content.

The app includes a FastAPI backend, a small web UI, automatic grading, and a
fallback mode so it still works without an API key.

Run it with:

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload
python serve_ui.py
```

# API Documentation

> TODO: expand once endpoints are implemented. FastAPI also auto-generates
> interactive docs at `/docs` (Swagger UI) once the server is running.

## Endpoints (planned)

### `POST /api/generation/`
Generate assessment questions for a given topic.

### `POST /api/grading/`
Grade a student answer against a rubric.

### `POST /api/explanation/`
Return an explanation (SHAP/LIME/Captum) for a grading decision.

### `GET /health`
Health check.

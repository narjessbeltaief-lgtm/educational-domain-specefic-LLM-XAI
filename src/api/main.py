"""
FastAPI application exposing the XAI educational assessment framework
as REST services, to be consumed by the Spring Boot platform.

Run locally with:
    uvicorn src.api.main:app --reload
"""

from fastapi import FastAPI

from src.api.routes import generation, grading, explanation

app = FastAPI(
    title="XAI Educational Assessment API",
    description=(
        "REST API exposing question generation, automated grading, and "
        "explainability endpoints for integration with the Spring Boot platform."
    ),
    version="0.1.0",
)

app.include_router(generation.router, prefix="/api/generation", tags=["generation"])
app.include_router(grading.router, prefix="/api/grading", tags=["grading"])
app.include_router(explanation.router, prefix="/api/explanation", tags=["explanation"])


@app.get("/health")
def health_check():
    return {"status": "ok"}

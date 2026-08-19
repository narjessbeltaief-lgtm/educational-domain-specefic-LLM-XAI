"""
FastAPI application exposing the XAI educational assessment framework
as REST services, to be consumed by the Spring Boot platform.

Run locally with:
	uvicorn src.api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import explanation, generation, grading, testing

app = FastAPI(
	title="XAI Educational Assessment API",
	description=(
		"REST API exposing question generation, automated grading, and "
		"explainability endpoints for integration with the Spring Boot platform."
	),
	version="0.1.0",
)

# The standalone demo web_ui.html is served from a different port
# (serve_ui.py, :8080) than the API (:8000), so it needs CORS enabled.
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(generation.router, prefix="/api/generation", tags=["generation"])
app.include_router(grading.router, prefix="/api/grading", tags=["grading"])
app.include_router(explanation.router, prefix="/api/explanation", tags=["explanation"])
app.include_router(testing.router, prefix="/api/testing", tags=["testing"])


@app.get("/health")
def health_check():
	return {"status": "ok"}

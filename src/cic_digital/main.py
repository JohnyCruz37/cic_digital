"""Aplicação FastAPI — ponto de entrada (health até implementação do núcleo /v1)."""

from fastapi import FastAPI

app = FastAPI(
    title="CIC Digital",
    description="API de leitura do Catecismo da Igreja Católica",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

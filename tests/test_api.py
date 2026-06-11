"""Smoke tests da infraestrutura HTTP."""

from fastapi.testclient import TestClient

from cic_digital.api.v1.read import get_read_index_service
from cic_digital.dtos.read_index import (
    IndexArticleDTO,
    IndexBookDTO,
    IndexChapterDTO,
    IndexPartDTO,
    IndexSectionDTO,
    IndexTitleDTO,
)
from cic_digital.main import app
from cic_digital.services.read_index_service import ReadIndexService

client = TestClient(app)


def _sample_index() -> IndexBookDTO:
    return IndexBookDTO(
        id=1,
        title="Catecismo da Igreja Católica",
        content_version="1",
        parts=[
            IndexPartDTO(
                id=10,
                kind="prologue",
                title="Prólogo",
                sort_order=0,
                sections=[
                    IndexSectionDTO(
                        id=20,
                        title="Seção",
                        sort_order=1,
                        chapters=[
                            IndexChapterDTO(
                                id=30,
                                title="Capítulo",
                                sort_order=1,
                                articles=[
                                    IndexArticleDTO(
                                        id=40,
                                        title="Artigo",
                                        sort_order=1,
                                        titles=[
                                            IndexTitleDTO(
                                                id=50,
                                                title="Título",
                                                sort_order=1,
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


class _StubReadIndexService(ReadIndexService):
    def __init__(self) -> None:
        pass

    def build_index(self) -> IndexBookDTO:
        return _sample_index()


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_health_includes_correlation_id_header():
    response = client.get("/health", headers={"X-Correlation-ID": "test-correlation-id"})
    assert response.headers.get("X-Correlation-ID") == "test-correlation-id"


def test_openapi_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/health" in schema["paths"]


def test_openapi_includes_read_index():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/api/v1/read/index" in schema["paths"]


def test_read_index_returns_envelope():
    app.dependency_overrides[get_read_index_service] = _StubReadIndexService
    try:
        response = client.get("/api/v1/read/index")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == 1
    assert body["data"]["parts"][0]["kind"] == "prologue"
    assert body["data"]["parts"][0]["sections"][0]["chapters"][0]["articles"][0]["titles"][0]["id"] == 50

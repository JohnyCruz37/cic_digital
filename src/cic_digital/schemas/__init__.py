"""Contratos HTTP da API (request/response).

Schemas definem o que entra e sai pelos endpoints (OpenAPI). Para dados
internos entre Service e Repository, use DTOs em `cic_digital.dtos`.
"""

from cic_digital.schemas.read_index import (
    IndexArticleData,
    IndexChapterData,
    IndexData,
    IndexPartData,
    IndexSectionData,
    IndexTitleData,
)
from cic_digital.schemas.response import (
    ErrorDetail,
    ErrorResponse,
    HealthData,
    MessageData,
    ReadyData,
    SuccessResponse,
)

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "HealthData",
    "IndexArticleData",
    "IndexChapterData",
    "IndexData",
    "IndexPartData",
    "IndexSectionData",
    "IndexTitleData",
    "MessageData",
    "ReadyData",
    "SuccessResponse",
]

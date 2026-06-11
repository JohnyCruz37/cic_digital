from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from cic_digital.core.logger import get_logger
from cic_digital.db.connection import get_db
from cic_digital.repositories.read_index_repository import ReadIndexRepository
from cic_digital.schemas.read_index import IndexData
from cic_digital.schemas.response import SuccessResponse
from cic_digital.services.read_index_service import ReadIndexService

logger = get_logger(__name__)

router = APIRouter()


def get_read_index_repository(
    session: Annotated[Session, Depends(get_db)],
) -> ReadIndexRepository:
    return ReadIndexRepository(session)


def get_read_index_service(
    repository: Annotated[ReadIndexRepository, Depends(get_read_index_repository)],
) -> ReadIndexService:
    return ReadIndexService(repository)


@router.get(
    "/index",
    response_model=SuccessResponse[IndexData],
    status_code=status.HTTP_200_OK,
    summary="Índice estrutural do Catecismo",
    description=(
        "Retorna a árvore de navegação completa (Book → Part → Section → "
        "Chapter → Article → Title), sem texto de parágrafos."
    ),
)
def get_read_index(
    service: Annotated[ReadIndexService, Depends(get_read_index_service)],
) -> SuccessResponse[IndexData]:
    logger.debug("Índice de leitura solicitado")
    index = service.build_index()
    return SuccessResponse(data=IndexData.model_validate(index.model_dump()))

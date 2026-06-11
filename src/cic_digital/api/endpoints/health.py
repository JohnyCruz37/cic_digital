from fastapi import APIRouter, status

from cic_digital.core.exceptions import ServiceUnavailableError
from cic_digital.core.logger import get_logger
from cic_digital.db.connection import db
from cic_digital.schemas.response import HealthData, ReadyData, SuccessResponse

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=SuccessResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
def health() -> SuccessResponse[HealthData]:
    logger.debug("Health check solicitado")
    return SuccessResponse(data=HealthData())


@router.get(
    "/ready",
    response_model=SuccessResponse[ReadyData],
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    responses={503: {"description": "Serviço indisponível"}},
)
def ready() -> SuccessResponse[ReadyData]:
    try:
        db.ping()
    except Exception as exc:
        logger.error("Readiness check falhou: %s", exc)
        raise ServiceUnavailableError("Banco de dados indisponível") from exc
    return SuccessResponse(data=ReadyData())

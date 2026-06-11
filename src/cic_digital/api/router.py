from fastapi import APIRouter

from cic_digital.api.endpoints.health import router as health_router
from cic_digital.api.v1.router import v1_router
from cic_digital.core.config import settings

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router, prefix=settings.api.prefix)

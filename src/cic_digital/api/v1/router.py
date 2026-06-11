from fastapi import APIRouter

from cic_digital.api.v1.read import router as read_router

v1_router = APIRouter()

v1_router.include_router(read_router, prefix="/read", tags=["read"])

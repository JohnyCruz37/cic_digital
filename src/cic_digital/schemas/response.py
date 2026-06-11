from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class HealthData(BaseModel):
    status: str = "ok"


class ReadyData(BaseModel):
    status: str = "ready"
    database: str = "connected"


class MessageData(BaseModel):
    message: str = Field(..., description="Mensagem informativa")

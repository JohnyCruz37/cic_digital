from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base para DTOs internos.

    DTOs transportam dados entre camadas (Repository ↔ Service) sem expor
    entidades ORM nem detalhes do contrato HTTP. Devem ser imutáveis e
    independentes da API.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

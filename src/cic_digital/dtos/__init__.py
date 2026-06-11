"""Objetos de transferência internos (DTOs).

Use DTOs para trafegar dados entre Repository e Service. Schemas (`schemas/`)
permanecem exclusivos para entrada e saída HTTP.
"""

from cic_digital.dtos.base import BaseDTO

__all__ = ["BaseDTO"]

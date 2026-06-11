from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from cic_digital.core.config import settings


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Gera JWT de acesso — preparado para autenticação futura."""
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.security.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida JWT de acesso."""
    try:
        return jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado") from exc

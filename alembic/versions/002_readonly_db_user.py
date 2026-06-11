"""Usuário read-only cic_read — permissões SELECT no schema content (ADR 007)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from cic_digital.core.config import settings
from cic_digital.models.constants import CONTENT_SCHEMA

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

READ_USER = settings.postgres_read_user
DB_NAME = settings.postgres_db


def _escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


def upgrade() -> None:
    password = _escape_sql_literal(settings.postgres_read_password)

    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{READ_USER}') THEN
                    CREATE ROLE {READ_USER} LOGIN PASSWORD '{password}';
                ELSE
                    ALTER ROLE {READ_USER} WITH PASSWORD '{password}';
                END IF;
            END
            $$;
            """
        )
    )

    op.execute(sa.text(f"GRANT CONNECT ON DATABASE {DB_NAME} TO {READ_USER}"))
    op.execute(sa.text(f"GRANT USAGE ON SCHEMA {CONTENT_SCHEMA} TO {READ_USER}"))
    op.execute(
        sa.text(
            f"GRANT SELECT ON ALL TABLES IN SCHEMA {CONTENT_SCHEMA} TO {READ_USER}"
        )
    )
    op.execute(
        sa.text(
            f"""
            ALTER DEFAULT PRIVILEGES IN SCHEMA {CONTENT_SCHEMA}
            GRANT SELECT ON TABLES TO {READ_USER}
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA {CONTENT_SCHEMA} FROM {READ_USER}"
        )
    )
    op.execute(
        sa.text(f"REVOKE USAGE ON SCHEMA {CONTENT_SCHEMA} FROM {READ_USER}")
    )
    op.execute(sa.text(f"REVOKE CONNECT ON DATABASE {DB_NAME} FROM {READ_USER}"))
    op.execute(sa.text(f"DROP ROLE IF EXISTS {READ_USER}"))

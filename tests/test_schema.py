"""Smoke tests — schema content (requer Postgres + migrations aplicadas)."""

import os

import pytest
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").lower() not in ("1", "true", "yes"),
    reason="Defina RUN_DB_TESTS=1 com Postgres disponível",
)


@pytest.fixture
def engine():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://cic:cic@localhost:5432/cic_digital",
    )
    return create_engine(url)


def test_content_schema_exists(engine):
    insp = inspect(engine)
    assert "content" in insp.get_schema_names()


def test_content_tables_exist(engine):
    insp = inspect(engine)
    tables = set(insp.get_table_names(schema="content"))
    expected = {
        "books",
        "parts",
        "sections",
        "chapters",
        "articles",
        "article_groups",
        "paragraphs",
        "alembic_version",
    }
    assert expected.issubset(tables)


def test_paragraphs_number_unique(engine):
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'content'
                  AND tablename = 'paragraphs'
                  AND indexdef LIKE '%UNIQUE%number%'
                """
            )
        ).fetchall()
    assert len(rows) >= 1

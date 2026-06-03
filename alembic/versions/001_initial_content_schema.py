"""Schema content inicial — CIC (ADR 003)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONTENT_SCHEMA = "content"


def upgrade() -> None:
    op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {CONTENT_SCHEMA}"))

    op.create_table(
        "books",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_format", sa.String(length=32), nullable=False),
        sa.Column("content_version", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema=CONTENT_SCHEMA,
    )

    op.create_table(
        "parts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_format", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["book_id"],
            [f"{CONTENT_SCHEMA}.books.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=CONTENT_SCHEMA,
    )

    op.create_table(
        "sections",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("part_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_format", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["part_id"],
            [f"{CONTENT_SCHEMA}.parts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=CONTENT_SCHEMA,
    )

    op.create_table(
        "chapters",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_format", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["section_id"],
            [f"{CONTENT_SCHEMA}.sections.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=CONTENT_SCHEMA,
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("chapter_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_format", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["chapter_id"],
            [f"{CONTENT_SCHEMA}.chapters.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=CONTENT_SCHEMA,
    )

    op.create_table(
        "article_groups",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_format", sa.String(length=32), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["article_id"],
            [f"{CONTENT_SCHEMA}.articles.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=CONTENT_SCHEMA,
    )

    op.create_table(
        "paragraphs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("article_group_id", sa.BigInteger(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_format", sa.String(length=32), nullable=False),
        sa.Column("references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("footnotes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["article_id"],
            [f"{CONTENT_SCHEMA}.articles.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["article_group_id"],
            [f"{CONTENT_SCHEMA}.article_groups.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number", name="uq_paragraphs_number"),
        schema=CONTENT_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("paragraphs", schema=CONTENT_SCHEMA)
    op.drop_table("article_groups", schema=CONTENT_SCHEMA)
    op.drop_table("articles", schema=CONTENT_SCHEMA)
    op.drop_table("chapters", schema=CONTENT_SCHEMA)
    op.drop_table("sections", schema=CONTENT_SCHEMA)
    op.drop_table("parts", schema=CONTENT_SCHEMA)
    op.drop_table("books", schema=CONTENT_SCHEMA)
    op.execute(sa.text(f"DROP SCHEMA IF EXISTS {CONTENT_SCHEMA} CASCADE"))

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cic_digital.models.base import Base
from cic_digital.models.constants import CONTENT_SCHEMA

SCHEMA = {"schema": CONTENT_SCHEMA}


class Book(Base):
    __tablename__ = "books"
    __table_args__ = SCHEMA

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_format: Mapped[str] = mapped_column(String(32), nullable=False)
    content_version: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    parts: Mapped[list["Part"]] = relationship(back_populates="book")


class Part(Base):
    __tablename__ = "parts"
    __table_args__ = SCHEMA

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    book_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.books.id", ondelete="RESTRICT"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_format: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    book: Mapped["Book"] = relationship(back_populates="parts")
    sections: Mapped[list["Section"]] = relationship(back_populates="part")


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = SCHEMA

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    part_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.parts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_format: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    part: Mapped["Part"] = relationship(back_populates="sections")
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="section")


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = SCHEMA

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.sections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_format: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    section: Mapped["Section"] = relationship(back_populates="chapters")
    articles: Mapped[list["Article"]] = relationship(back_populates="chapter")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = SCHEMA

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.chapters.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_format: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    chapter: Mapped["Chapter"] = relationship(back_populates="articles")
    groups: Mapped[list["ArticleGroup"]] = relationship(back_populates="article")
    paragraphs: Mapped[list["Paragraph"]] = relationship(back_populates="article")


class ArticleGroup(Base):
    __tablename__ = "article_groups"
    __table_args__ = SCHEMA

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.articles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_format: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    article: Mapped["Article"] = relationship(back_populates="groups")
    paragraphs: Mapped[list["Paragraph"]] = relationship(back_populates="article_group")


class Paragraph(Base):
    __tablename__ = "paragraphs"
    __table_args__ = (
        UniqueConstraint("number", name="uq_paragraphs_number"),
        SCHEMA,
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.articles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    article_group_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{CONTENT_SCHEMA}.article_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_format: Mapped[str] = mapped_column(String(32), nullable=False)
    references_: Mapped[dict | None] = mapped_column("references", JSONB, nullable=True)
    footnotes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    article: Mapped["Article"] = relationship(back_populates="paragraphs")
    article_group: Mapped["ArticleGroup | None"] = relationship(
        back_populates="paragraphs",
    )

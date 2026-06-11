from dataclasses import dataclass

from sqlalchemy import select

from cic_digital.models.content import (
    Article,
    ArticleGroup,
    Book,
    Chapter,
    Part,
    Section,
)
from cic_digital.repositories.base import BaseRepository


@dataclass(frozen=True)
class ReadIndexRawData:
    book: Book | None
    parts: list[Part]
    sections: list[Section]
    chapters: list[Chapter]
    articles: list[Article]
    titles: list[ArticleGroup]


class ReadIndexRepository(BaseRepository):
    """Consultas planas em lote para montagem do índice de navegação."""

    def fetch_index_data(self) -> ReadIndexRawData:
        book = self._session.scalar(select(Book).order_by(Book.id).limit(1))
        if book is None:
            return ReadIndexRawData(
                book=None,
                parts=[],
                sections=[],
                chapters=[],
                articles=[],
                titles=[],
            )

        parts = list(
            self._session.scalars(
                select(Part)
                .where(Part.book_id == book.id)
                .order_by(Part.sort_order)
            ).all()
        )
        part_ids = [part.id for part in parts]

        sections: list[Section] = []
        if part_ids:
            sections = list(
                self._session.scalars(
                    select(Section)
                    .where(Section.part_id.in_(part_ids))
                    .order_by(Section.sort_order)
                ).all()
            )
        section_ids = [section.id for section in sections]

        chapters: list[Chapter] = []
        if section_ids:
            chapters = list(
                self._session.scalars(
                    select(Chapter)
                    .where(Chapter.section_id.in_(section_ids))
                    .order_by(Chapter.sort_order)
                ).all()
            )
        chapter_ids = [chapter.id for chapter in chapters]

        articles: list[Article] = []
        if chapter_ids:
            articles = list(
                self._session.scalars(
                    select(Article)
                    .where(Article.chapter_id.in_(chapter_ids))
                    .order_by(Article.sort_order)
                ).all()
            )
        article_ids = [article.id for article in articles]

        titles: list[ArticleGroup] = []
        if article_ids:
            titles = list(
                self._session.scalars(
                    select(ArticleGroup)
                    .where(
                        ArticleGroup.article_id.in_(article_ids),
                        ArticleGroup.level == 2,
                    )
                    .order_by(ArticleGroup.sort_order)
                ).all()
            )

        return ReadIndexRawData(
            book=book,
            parts=parts,
            sections=sections,
            chapters=chapters,
            articles=articles,
            titles=titles,
        )

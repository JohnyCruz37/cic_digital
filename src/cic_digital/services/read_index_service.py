from collections import defaultdict
from collections.abc import Iterable
from typing import TypeVar

from cic_digital.core.exceptions import NotFoundError
from cic_digital.dtos.read_index import (
    IndexArticleDTO,
    IndexBookDTO,
    IndexChapterDTO,
    IndexPartDTO,
    IndexSectionDTO,
    IndexTitleDTO,
)
from cic_digital.models.content import (
    Article,
    ArticleGroup,
    Chapter,
    Part,
    Section,
)
from cic_digital.repositories.read_index_repository import (
    ReadIndexRawData,
    ReadIndexRepository,
)
from cic_digital.services.base import BaseService

T = TypeVar("T")


class ReadIndexService(BaseService):
    def build_index(self) -> IndexBookDTO:
        raw = self._repository.fetch_index_data()
        if raw.book is None:
            raise NotFoundError("Conteúdo não encontrado")

        titles_by_article = _group_by(raw.titles, lambda title: title.article_id)
        articles_by_chapter = _group_by(raw.articles, lambda article: article.chapter_id)
        chapters_by_section = _group_by(raw.chapters, lambda chapter: chapter.section_id)
        sections_by_part = _group_by(raw.sections, lambda section: section.part_id)

        parts = sorted(raw.parts, key=lambda part: part.sort_order)
        parts = [
            _build_part(
                part,
                sections_by_part.get(part.id, []),
                chapters_by_section,
                articles_by_chapter,
                titles_by_article,
            )
            for part in parts
        ]

        return IndexBookDTO(
            id=raw.book.id,
            title=raw.book.title,
            content_version=raw.book.content_version,
            parts=parts,
        )


def _group_by(items: Iterable[T], key_fn) -> dict[int, list[T]]:
    grouped: dict[int, list[T]] = defaultdict(list)
    for item in items:
        grouped[key_fn(item)].append(item)
    for key in grouped:
        grouped[key].sort(key=lambda item: item.sort_order)
    return grouped


def _build_part(
    part: Part,
    sections: list[Section],
    chapters_by_section: dict[int, list[Chapter]],
    articles_by_chapter: dict[int, list[Article]],
    titles_by_article: dict[int, list[ArticleGroup]],
) -> IndexPartDTO:
    return IndexPartDTO(
        id=part.id,
        kind=part.kind,
        title=part.title,
        sort_order=part.sort_order,
        sections=[
            _build_section(
                section,
                chapters_by_section.get(section.id, []),
                articles_by_chapter,
                titles_by_article,
            )
            for section in sections
        ],
    )


def _build_section(
    section: Section,
    chapters: list[Chapter],
    articles_by_chapter: dict[int, list[Article]],
    titles_by_article: dict[int, list[ArticleGroup]],
) -> IndexSectionDTO:
    return IndexSectionDTO(
        id=section.id,
        title=section.title,
        sort_order=section.sort_order,
        chapters=[
            _build_chapter(chapter, articles_by_chapter, titles_by_article)
            for chapter in chapters
        ],
    )


def _build_chapter(
    chapter: Chapter,
    articles_by_chapter: dict[int, list[Article]],
    titles_by_article: dict[int, list[ArticleGroup]],
) -> IndexChapterDTO:
    return IndexChapterDTO(
        id=chapter.id,
        title=chapter.title,
        sort_order=chapter.sort_order,
        articles=[
            _build_article(article, titles_by_article.get(article.id, []))
            for article in articles_by_chapter.get(chapter.id, [])
        ],
    )


def _build_article(
    article: Article,
    titles: list[ArticleGroup],
) -> IndexArticleDTO:
    return IndexArticleDTO(
        id=article.id,
        title=article.title,
        sort_order=article.sort_order,
        titles=[
            IndexTitleDTO(
                id=title.id,
                title=title.title,
                sort_order=title.sort_order,
            )
            for title in titles
        ],
    )

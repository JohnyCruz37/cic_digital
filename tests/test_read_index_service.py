from unittest.mock import MagicMock

import pytest

from cic_digital.core.exceptions import NotFoundError
from cic_digital.dtos.read_index import IndexBookDTO
from cic_digital.models.content import (
    Article,
    ArticleGroup,
    Book,
    Chapter,
    Part,
    Section,
)
from cic_digital.repositories.read_index_repository import ReadIndexRawData
from cic_digital.services.read_index_service import ReadIndexService


def _make_book() -> Book:
    book = MagicMock(spec=Book)
    book.id = 1
    book.title = "Catecismo da Igreja Católica"
    book.content_version = "1"
    return book


def _make_part(part_id: int, sort_order: int, kind: str = "part") -> Part:
    part = MagicMock(spec=Part)
    part.id = part_id
    part.kind = kind
    part.title = f"Parte {part_id}"
    part.sort_order = sort_order
    return part


def _make_section(section_id: int, part_id: int, sort_order: int) -> Section:
    section = MagicMock(spec=Section)
    section.id = section_id
    section.part_id = part_id
    section.title = f"Seção {section_id}"
    section.sort_order = sort_order
    return section


def _make_chapter(chapter_id: int, section_id: int, sort_order: int) -> Chapter:
    chapter = MagicMock(spec=Chapter)
    chapter.id = chapter_id
    chapter.section_id = section_id
    chapter.title = f"Capítulo {chapter_id}"
    chapter.sort_order = sort_order
    return chapter


def _make_article(article_id: int, chapter_id: int, sort_order: int) -> Article:
    article = MagicMock(spec=Article)
    article.id = article_id
    article.chapter_id = chapter_id
    article.title = f"Artigo {article_id}"
    article.sort_order = sort_order
    return article


def _make_title(title_id: int, article_id: int, sort_order: int, level: int = 2) -> ArticleGroup:
    title = MagicMock(spec=ArticleGroup)
    title.id = title_id
    title.article_id = article_id
    title.title = f"Título {title_id}"
    title.sort_order = sort_order
    title.level = level
    return title


def _make_raw_data() -> ReadIndexRawData:
    return ReadIndexRawData(
        book=_make_book(),
        parts=[_make_part(10, sort_order=2), _make_part(11, sort_order=1, kind="prologue")],
        sections=[_make_section(20, part_id=10, sort_order=1)],
        chapters=[_make_chapter(30, section_id=20, sort_order=1)],
        articles=[
            _make_article(40, chapter_id=30, sort_order=2),
            _make_article(41, chapter_id=30, sort_order=1),
        ],
        titles=[
            _make_title(50, article_id=40, sort_order=2),
            _make_title(51, article_id=40, sort_order=1),
        ],
    )


def test_build_index_raises_when_book_missing():
    repository = MagicMock()
    repository.fetch_index_data.return_value = ReadIndexRawData(
        book=None,
        parts=[],
        sections=[],
        chapters=[],
        articles=[],
        titles=[],
    )
    service = ReadIndexService(repository)

    with pytest.raises(NotFoundError, match="Conteúdo não encontrado"):
        service.build_index()


def test_build_index_assembles_hierarchy():
    repository = MagicMock()
    repository.fetch_index_data.return_value = _make_raw_data()
    service = ReadIndexService(repository)

    index = service.build_index()

    assert isinstance(index, IndexBookDTO)
    assert index.id == 1
    assert len(index.parts) == 2
    assert index.parts[0].kind == "prologue"
    assert index.parts[1].kind == "part"
    assert index.parts[1].sections[0].chapters[0].articles[0].id == 41
    assert index.parts[1].sections[0].chapters[0].articles[1].titles[0].id == 51
    assert index.parts[1].sections[0].chapters[0].articles[1].titles[1].id == 50


def test_build_index_uses_titles_returned_by_repository():
    repository = MagicMock()
    repository.fetch_index_data.return_value = _make_raw_data()
    service = ReadIndexService(repository)

    index = service.build_index()
    article = index.parts[1].sections[0].chapters[0].articles[1]

    assert len(article.titles) == 2
    assert [title.id for title in article.titles] == [51, 50]

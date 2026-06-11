from cic_digital.dtos.base import BaseDTO


class IndexTitleDTO(BaseDTO):
    id: int
    title: str
    sort_order: int


class IndexArticleDTO(BaseDTO):
    id: int
    title: str
    sort_order: int
    titles: list[IndexTitleDTO]


class IndexChapterDTO(BaseDTO):
    id: int
    title: str
    sort_order: int
    articles: list[IndexArticleDTO]


class IndexSectionDTO(BaseDTO):
    id: int
    title: str
    sort_order: int
    chapters: list[IndexChapterDTO]


class IndexPartDTO(BaseDTO):
    id: int
    kind: str
    title: str
    sort_order: int
    sections: list[IndexSectionDTO]


class IndexBookDTO(BaseDTO):
    id: int
    title: str
    content_version: str
    parts: list[IndexPartDTO]

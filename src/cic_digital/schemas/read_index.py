from pydantic import BaseModel, Field


class IndexTitleData(BaseModel):
    id: int
    title: str
    sort_order: int


class IndexArticleData(BaseModel):
    id: int
    title: str
    sort_order: int
    titles: list[IndexTitleData] = Field(default_factory=list)


class IndexChapterData(BaseModel):
    id: int
    title: str
    sort_order: int
    articles: list[IndexArticleData] = Field(default_factory=list)


class IndexSectionData(BaseModel):
    id: int
    title: str
    sort_order: int
    chapters: list[IndexChapterData] = Field(default_factory=list)


class IndexPartData(BaseModel):
    id: int
    kind: str
    title: str
    sort_order: int
    sections: list[IndexSectionData] = Field(default_factory=list)


class IndexData(BaseModel):
    id: int
    title: str
    content_version: str
    parts: list[IndexPartData] = Field(default_factory=list)

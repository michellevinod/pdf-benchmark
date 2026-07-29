from typing import Any

from pydantic import BaseModel


class Page(BaseModel):
    page_number: int | None

    text: str
    markdown: str

    tables: list[Any]
    images: list[Any]
    figures: list[Any]
    layout_blocks: list[Any]

    ocr_text: str

    metadata: dict[str, Any]


class Statistics(BaseModel):
    page_count: int | None

    table_count: int

    image_count: int


class NormalizedDocument(BaseModel):
    parser: str

    source_pdf: str

    metadata: dict[str, Any]

    pages: list[Page]

    statistics: Statistics
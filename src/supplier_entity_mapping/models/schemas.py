from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    file_name: str | None = Field(
        default=None,
        description="Optional file name inside the vendor data directory.",
    )


class IndexResponse(BaseModel):
    status: str
    file_name: str
    rows_indexed: int
    collection_name: str
    persist_directory: str


class SearchResult(BaseModel):
    rank: int
    vendor_name: str
    summary: str
    reason: str | None = None
    metadata: dict[str, Any]
    score: float | None = None


class SearchResponse(BaseModel):
    query: str
    total_returned: int
    results: list[SearchResult]
    grounded_by_llm: bool


class LlmSearchSelection(BaseModel):
    vendor_name: str
    reason: str
    source_row_number: int | None = None


class LlmSearchResponse(BaseModel):
    results: list[LlmSearchSelection]

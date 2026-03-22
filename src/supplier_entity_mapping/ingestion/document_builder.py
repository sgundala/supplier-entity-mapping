from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.documents import Document


def _normalize_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _row_to_metadata(row: pd.Series) -> dict[str, Any]:
    return {
        str(column): _normalize_value(value)
        for column, value in row.items()
        if _normalize_value(value)
    }


def _row_to_page_content(metadata: dict[str, Any]) -> str:
    lines = [f"{key}: {value}" for key, value in metadata.items()]
    return "\n".join(lines)


def build_documents(dataframe: pd.DataFrame) -> list[Document]:
    documents: list[Document] = []
    for row_index, (_, row) in enumerate(dataframe.iterrows(), start=1):
        metadata = _row_to_metadata(row)
        if not metadata:
            continue

        metadata["source_row_number"] = row_index
        documents.append(
            Document(
                page_content=_row_to_page_content(metadata),
                metadata=metadata,
            )
        )

    if not documents:
        raise ValueError("No non-empty supplier rows were available to index.")

    return documents

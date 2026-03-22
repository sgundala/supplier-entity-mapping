import pandas as pd

from supplier_entity_mapping.ingestion.document_builder import build_documents


def test_build_documents_creates_one_document_per_row() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "supplier_name": "ABC Chemicals",
                "category": "Industrial Chemicals",
                "country": "USA",
            },
            {
                "supplier_name": "Northwind Logistics",
                "category": "Logistics",
                "country": "USA",
            },
        ]
    )

    documents = build_documents(dataframe)

    assert len(documents) == 2
    assert documents[0].metadata["supplier_name"] == "ABC Chemicals"
    assert documents[0].metadata["source_row_number"] == 1
    assert "category: Industrial Chemicals" in documents[0].page_content


def test_build_documents_skips_empty_rows_and_preserves_row_number() -> None:
    dataframe = pd.DataFrame(
        [
            {"supplier_name": "", "category": "", "country": ""},
            {
                "supplier_name": "GreenSteel Components",
                "category": "Manufacturing",
                "country": "USA",
            },
        ]
    )

    documents = build_documents(dataframe)

    assert len(documents) == 1
    assert documents[0].metadata["source_row_number"] == 2

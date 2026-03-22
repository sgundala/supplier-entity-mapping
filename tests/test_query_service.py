from supplier_entity_mapping.config import AppSettings
from supplier_entity_mapping.models.schemas import (
    LlmSearchResponse,
    LlmSearchSelection,
    SearchResult,
)
from supplier_entity_mapping.rag.query_service import QueryService


def test_metadata_match_results_prioritize_exact_category_matches() -> None:
    service = QueryService(AppSettings())

    class FakeVectorStore:
        def get(self, include):
            return {
                "documents": [
                    "supplier_name: Gamma Pharmaceuticals\nclient_category: SUPPLY CHAIN",
                    "supplier_name: Beta Labs LLC\nclient_category: MARKETING",
                ],
                "metadatas": [
                    {
                        "supplier_name": "Gamma Pharmaceuticals",
                        "client_category": "SUPPLY CHAIN",
                        "source_row_number": 35,
                    },
                    {
                        "supplier_name": "Beta Labs LLC",
                        "client_category": "MARKETING",
                        "source_row_number": 3,
                    },
                ],
            }

    service._vector_store = lambda: FakeVectorStore()  # type: ignore[method-assign]

    results = service._metadata_match_results("marketing")

    assert len(results) == 1
    assert results[0].vendor_name == "Beta Labs LLC"
    assert results[0].metadata["client_category"] == "MARKETING"


def test_llm_rank_results_renumbers_after_duplicate_skips() -> None:
    service = QueryService(AppSettings(GROQ_API_KEY="test-key"))
    candidates = [
        SearchResult(
            rank=1,
            vendor_name="Gamma Pharmaceuticals",
            summary="a",
            metadata={"source_row_number": 35},
            score=0.5,
        ),
        SearchResult(
            rank=6,
            vendor_name="Gamma Pharma Ltd",
            summary="b",
            metadata={"source_row_number": 4},
            score=0.4,
        ),
    ]

    selections = LlmSearchResponse(
        results=[
            LlmSearchSelection(
                vendor_name="Gamma Pharmaceuticals",
                reason="Exact match",
                source_row_number=35,
            ),
            LlmSearchSelection(
                vendor_name="Gamma Pharmaceuticals",
                reason="Duplicate",
                source_row_number=35,
            ),
            LlmSearchSelection(
                vendor_name="Gamma Pharma Ltd",
                reason="Close match",
                source_row_number=4,
            ),
        ]
    )

    service._parse_json_payload = lambda content: selections.model_dump()  # type: ignore[method-assign]

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, prompt):
            class Response:
                content = '{"results":[]}'

            return Response()

    import supplier_entity_mapping.rag.query_service as query_service_module

    original_chat_groq = query_service_module.ChatGroq
    query_service_module.ChatGroq = FakeGroq
    try:
        ranked = service._llm_rank_results("marketing", candidates)
    finally:
        query_service_module.ChatGroq = original_chat_groq

    assert [item.rank for item in ranked] == [1, 2]
    assert [item.vendor_name for item in ranked] == [
        "Gamma Pharmaceuticals",
        "Gamma Pharma Ltd",
    ]

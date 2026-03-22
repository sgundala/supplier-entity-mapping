from fastapi.testclient import TestClient

from supplier_entity_mapping.api.dependencies import get_index_service, get_query_service
from supplier_entity_mapping.main import app
from supplier_entity_mapping.models.schemas import IndexResponse, SearchResponse, SearchResult


class StubIndexService:
    def __init__(self) -> None:
        self.indexed = False

    def build_index(self, payload):
        self.indexed = True
        return IndexResponse(
            status="indexed",
            file_name=payload.file_name or "vendors.csv",
            rows_indexed=3,
            collection_name="supplier_documents",
            persist_directory="storage/chroma",
        )

    def has_indexed_data(self) -> bool:
        return True


class StubQueryService:
    def search(self, query: str) -> SearchResponse:
        return SearchResponse(
            query=query,
            total_returned=1,
            grounded_by_llm=False,
            results=[
                SearchResult(
                    rank=1,
                    vendor_name="ABC Chemicals",
                    summary="Industrial chemicals supplier",
                    reason="Closest semantic match for the procurement query.",
                    metadata={"location": "Houston, TX"},
                    score=0.99,
                )
            ],
        )


def test_index_endpoint_returns_summary_shape() -> None:
    app.dependency_overrides[get_index_service] = lambda: StubIndexService()
    client = TestClient(app)

    response = client.post("/index", json={"file_name": "vendors.csv"})

    assert response.status_code == 200
    assert response.json()["rows_indexed"] == 3

    app.dependency_overrides.clear()


def test_search_endpoint_returns_top_results_shape() -> None:
    app.dependency_overrides[get_index_service] = lambda: StubIndexService()
    app.dependency_overrides[get_query_service] = lambda: StubQueryService()
    client = TestClient(app)

    response = client.get("/search", params={"q": "industrial chemicals supplier"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "industrial chemicals supplier"
    assert payload["total_returned"] == 1
    assert payload["results"][0]["vendor_name"] == "ABC Chemicals"
    assert payload["results"][0]["metadata"]["location"] == "Houston, TX"

    app.dependency_overrides.clear()

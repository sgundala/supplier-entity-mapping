from fastapi import APIRouter, Depends, HTTPException, Query

from supplier_entity_mapping.api.dependencies import get_index_service, get_query_service
from supplier_entity_mapping.models.schemas import IndexRequest, IndexResponse, SearchResponse
from supplier_entity_mapping.rag.query_service import QueryService
from supplier_entity_mapping.services.index_service import IndexService

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/index", response_model=IndexResponse)
def index_vendor_data(
    payload: IndexRequest,
    index_service: IndexService = Depends(get_index_service),  # noqa: B008
) -> IndexResponse:
    try:
        return index_service.build_index(payload)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/search", response_model=SearchResponse)
def search_suppliers(
    q: str = Query(..., min_length=2, description="Procurement query text."),
    query_service: QueryService = Depends(get_query_service),  # noqa: B008
    index_service: IndexService = Depends(get_index_service),  # noqa: B008
) -> SearchResponse:
    if not index_service.has_indexed_data():
        raise HTTPException(
            status_code=400,
            detail="No supplier index found. Run POST /index first.",
        )

    try:
        return query_service.search(q)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

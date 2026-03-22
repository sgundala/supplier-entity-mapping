from functools import lru_cache

from supplier_entity_mapping.config import AppSettings, get_settings
from supplier_entity_mapping.rag.query_service import QueryService
from supplier_entity_mapping.services.index_service import IndexService


@lru_cache(maxsize=1)
def get_index_service() -> IndexService:
    settings: AppSettings = get_settings()
    return IndexService(settings)


@lru_cache(maxsize=1)
def get_query_service() -> QueryService:
    settings: AppSettings = get_settings()
    return QueryService(settings)

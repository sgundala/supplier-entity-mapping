from __future__ import annotations

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from supplier_entity_mapping.config import AppSettings
from supplier_entity_mapping.ingestion import (
    build_documents,
    load_tabular_file,
    resolve_vendor_file,
)
from supplier_entity_mapping.models.schemas import IndexRequest, IndexResponse


class IndexService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._embeddings: HuggingFaceEmbeddings | None = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.settings.embedding_model_name,
                model_kwargs={"local_files_only": self.settings.hf_local_files_only},
            )
        return self._embeddings

    def _vector_store(self) -> Chroma:
        return Chroma(
            collection_name=self.settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_persist_dir),
        )

    def build_index(self, request: IndexRequest) -> IndexResponse:
        vendor_file = resolve_vendor_file(self.settings.vendor_data_dir, request.file_name)
        dataframe = load_tabular_file(vendor_file)
        documents = build_documents(dataframe)

        vector_store = self._vector_store()
        vector_store.reset_collection()
        vector_store.add_documents(documents=documents)

        return IndexResponse(
            status="indexed",
            file_name=vendor_file.name,
            rows_indexed=len(documents),
            collection_name=self.settings.chroma_collection_name,
            persist_directory=str(self.settings.chroma_persist_dir),
        )

    def has_indexed_data(self) -> bool:
        client = chromadb.PersistentClient(path=str(self.settings.chroma_persist_dir))
        collection = client.get_or_create_collection(name=self.settings.chroma_collection_name)
        return collection.count() > 0

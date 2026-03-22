import pandas as pd

from supplier_entity_mapping.config import AppSettings
from supplier_entity_mapping.models.schemas import IndexRequest
from supplier_entity_mapping.services.index_service import IndexService


class FakeVectorStore:
    def __init__(self) -> None:
        self.documents = []
        self.reset_called = False

    def reset_collection(self) -> None:
        self.reset_called = True

    def add_documents(self, documents) -> None:
        self.documents.extend(documents)


def test_build_index_indexes_documents_without_real_embeddings(tmp_path, monkeypatch) -> None:
    vendor_file = tmp_path / "vendors.csv"
    vendor_file.write_text(
        "supplier_name,category,country\nABC Chemicals,Industrial Chemicals,USA\n",
        encoding="utf-8",
    )

    fake_store = FakeVectorStore()
    settings = AppSettings(
        VENDOR_DATA_DIR=tmp_path,
        CHROMA_PERSIST_DIR=tmp_path / "chroma",
    )
    service = IndexService(settings)

    monkeypatch.setattr(service, "_vector_store", lambda: fake_store)

    response = service.build_index(IndexRequest(file_name="vendors.csv"))

    assert response.status == "indexed"
    assert response.rows_indexed == 1
    assert fake_store.reset_called is True
    assert fake_store.documents[0].metadata["supplier_name"] == "ABC Chemicals"


def test_build_index_rejects_empty_files(tmp_path) -> None:
    vendor_file = tmp_path / "vendors.csv"
    pd.DataFrame(columns=["supplier_name", "category"]).to_csv(vendor_file, index=False)

    settings = AppSettings(
        VENDOR_DATA_DIR=tmp_path,
        CHROMA_PERSIST_DIR=tmp_path / "chroma",
    )
    service = IndexService(settings)

    try:
        service.build_index(IndexRequest(file_name="vendors.csv"))
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Expected an empty vendor file to raise ValueError.")


def test_build_index_rejects_paths_outside_vendor_directory(tmp_path) -> None:
    outside_file = tmp_path.parent / "outside.csv"
    outside_file.write_text("supplier_name\nSecret Vendor\n", encoding="utf-8")

    settings = AppSettings(
        VENDOR_DATA_DIR=tmp_path,
        CHROMA_PERSIST_DIR=tmp_path / "chroma",
    )
    service = IndexService(settings)

    try:
        service.build_index(IndexRequest(file_name="../outside.csv"))
    except ValueError as exc:
        assert "inside the configured vendor data directory" in str(exc)
    else:
        raise AssertionError("Expected path traversal input to raise ValueError.")

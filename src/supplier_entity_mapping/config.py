from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model_name: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL_NAME")
    embedding_model_name: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    hf_local_files_only: bool = Field(default=False, alias="HF_LOCAL_FILES_ONLY")
    vendor_data_dir: Path = Field(default=Path("data/raw"), alias="VENDOR_DATA_DIR")
    chroma_persist_dir: Path = Field(default=Path("storage/chroma"), alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(
        default="supplier_documents",
        alias="CHROMA_COLLECTION_NAME",
    )
    frontend_dist_dir: Path = Field(default=Path("frontend/dist"), alias="FRONTEND_DIST_DIR")
    retrieval_top_k: int = Field(default=10, alias="RETRIEVAL_TOP_K")
    result_limit: int = Field(default=5, alias="RESULT_LIMIT")
    frontend_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="FRONTEND_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.vendor_data_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return settings

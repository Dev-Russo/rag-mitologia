from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-haiku-4-5"
    chroma_path: Path = Path("./chroma_db")
    chroma_collection: str = "bulfinch_mythology"
    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    pdf_path: Path = Path("./data/bulfinch-mythology.pdf")
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_min_score: float = Field(default=0.45, ge=0.0, le=1.0)
    max_retrieval_attempts: int = Field(default=3, ge=1, le=5)


@lru_cache
def get_settings() -> Settings:
    return Settings()

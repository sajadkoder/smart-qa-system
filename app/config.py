from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Smart QA System"
    app_version: str = "0.1.0"
    openai_api_key: str | None = None
    model_name: str = "gpt-4.1-mini"
    chunk_size: int = 700
    chunk_overlap: int = 120
    top_k: int = 3
    max_file_size_mb: int = 10
    upload_dir: Path = BASE_DIR / "data" / "uploads"
    document_dir: Path = BASE_DIR / "data" / "documents"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.document_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings

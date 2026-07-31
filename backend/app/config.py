"""AIGBooks 后端配置（pydantic-settings）。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，环境变量前缀 AIGBOOKS_。"""

    model_config = SettingsConfigDict(
        env_prefix="AIGBOOKS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://aigbooks:aigbooks@localhost:5432/aigbooks"
    evidence_dir: Path = Path("./var/evidence")
    covers_dir: Path = Path("./var/covers")

    max_upload_size: int = 20 * 1024 * 1024
    allowed_mime_types: list[str] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp", "video/mp4"]
    )

    report_rate_limit: int = 5
    report_rate_window: int = 3600

    page_size: int = 20

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例 Settings 工厂。"""
    return Settings()

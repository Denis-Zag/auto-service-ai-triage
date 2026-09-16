from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения."""

    app_name: str = "Auto Service AI Triage"
    proxyapi_key: str | None = None
    proxyapi_base_url: str = "https://api.proxyapi.ru/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 30.0
    database_backend: Literal["sqlite", "turso"] = "sqlite"
    database_path: Path = Path("data/triage.db")
    turso_database_url: str | None = None
    turso_auth_token: str | None = None
    requests_per_minute: int = 10
    use_llm: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Возвращает единственный экземпляр настроек."""

    return Settings()

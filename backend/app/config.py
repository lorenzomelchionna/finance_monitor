"""Application settings.

Single source of truth for config. Kept intentionally small for v1 —
single-user, local execution, no auth, no deploy.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FM_", env_file=".env", extra="ignore")

    base_currency: str = "EUR"
    database_url: str = "sqlite:///./finance_monitor.db"
    default_price_provider: str = "yfinance"
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

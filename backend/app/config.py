"""Application settings.

Single source of truth for config. Kept intentionally small for v1 —
single-user, local execution, no auth, no deploy.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor persisted data to a fixed dir under the backend root, resolved
# absolutely so the DB file is the same regardless of the process CWD.
# A relative "./finance_monitor.db" would silently create a fresh empty
# DB whenever uvicorn is launched from a different directory.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FM_", env_file=".env", extra="ignore")

    base_currency: str = "EUR"
    database_url: str = f"sqlite:///{DATA_DIR / 'finance_monitor.db'}"
    default_price_provider: str = "yfinance"
    # Both hostnames are covered since browsers treat localhost and
    # 127.0.0.1 as distinct origins for CORS purposes.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

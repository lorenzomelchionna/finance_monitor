"""Application settings.

Single source of truth for config. Single-user, no multi-tenancy — but
it now also runs deployed, so it carries the auth and data-location
knobs the platform needs.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor persisted data to an absolute dir so the DB file is the same
# regardless of the process CWD — a relative path would silently create
# a fresh empty DB when the server is launched from elsewhere.
# FM_DATA_DIR points at the mounted volume when deployed: the container
# filesystem is ephemeral, so without a volume the DB dies each deploy.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FM_DATA_DIR") or (BACKEND_ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FM_", env_file=".env", extra="ignore")

    base_currency: str = "EUR"
    database_url: str = f"sqlite:///{DATA_DIR / 'finance_monitor.db'}"
    default_price_provider: str = "yfinance"
    default_composition_provider: str = "justetf"

    # Auth. `password` empty => gate disabled (local dev only).
    # `require_auth` makes an empty password a hard startup failure, so a
    # deployed instance can never come up unprotected by accident.
    username: str = "lorenzo"
    password: str = ""
    require_auth: bool = False

    # Credentials set through a shell or a dashboard field routinely pick
    # up a trailing newline or stray spaces. A browser can't send those in
    # a Basic Auth header, so an untrimmed value locks the user out of
    # their own app with no useful error. Trim both sides.
    @field_validator("username", "password", mode="after")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()

    # Serve the built frontend from this process (single service, less
    # RAM than a second one). Empty => API only, as in local dev where
    # Vite serves the UI.
    static_dir: str = ""

    # Both hostnames are covered since browsers treat localhost and
    # 127.0.0.1 as distinct origins for CORS purposes. Irrelevant when
    # the frontend is served same-origin from static_dir.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

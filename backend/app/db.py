"""Database engine and session management (SQLite via SQLModel)."""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

# check_same_thread=False: SQLite + FastAPI's per-request threading model.
# Safe for our single-user local use case (no concurrent writers).
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Create tables from metadata. Used for dev/test convenience;
    schema evolution in real use goes through Alembic migrations."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

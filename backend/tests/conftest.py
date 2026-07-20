"""Shared pytest fixtures.

Every test gets an isolated in-memory SQLite DB via a StaticPool-backed
engine (so the same in-memory connection is reused across the session
fixture) — no dependency on the dev finance_monitor.db file.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

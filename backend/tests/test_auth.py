"""The app holds real financial data and is reachable from the public
internet once deployed, so these tests guard the password gate itself."""

import base64

import pytest
from fastapi.testclient import TestClient

from app.auth import basic_auth_middleware, require_password_configured
from app.config import get_settings
from app.main import app


def _auth(user: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def protected(monkeypatch):
    """Turn the gate on for one test (settings are lru_cached)."""
    get_settings.cache_clear()
    monkeypatch.setenv("FM_PASSWORD", "s3cret")
    monkeypatch.setenv("FM_USERNAME", "lorenzo")
    # The middleware warns only once per process; reset so state doesn't leak.
    if hasattr(basic_auth_middleware, "_warned"):
        del basic_auth_middleware._warned
    yield TestClient(app)
    get_settings.cache_clear()


def test_rejects_missing_credentials(protected):
    resp = protected.get("/api/holdings")
    assert resp.status_code == 401
    # Prompts the browser's native login dialog.
    assert resp.headers["www-authenticate"].startswith("Basic")


def test_rejects_wrong_password(protected):
    assert protected.get("/api/holdings", headers=_auth("lorenzo", "nope")).status_code == 401


def test_rejects_wrong_username(protected):
    assert protected.get("/api/holdings", headers=_auth("intruder", "s3cret")).status_code == 401


def test_accepts_correct_credentials(protected):
    assert protected.get("/api/holdings", headers=_auth("lorenzo", "s3cret")).status_code == 200


def test_health_is_exempt_so_platform_probes_work(protected):
    assert protected.get("/health").status_code == 200


def test_disabled_when_no_password_configured(monkeypatch):
    """Local dev convenience — must stay off only when FM_PASSWORD is unset."""
    get_settings.cache_clear()
    monkeypatch.delenv("FM_PASSWORD", raising=False)
    monkeypatch.setenv("FM_REQUIRE_AUTH", "false")
    if hasattr(basic_auth_middleware, "_warned"):
        del basic_auth_middleware._warned
    client = TestClient(app)
    assert client.get("/api/holdings").status_code == 200
    get_settings.cache_clear()


def test_startup_fails_if_auth_required_but_password_missing(monkeypatch):
    """A deployed instance must crash rather than come up unprotected."""
    get_settings.cache_clear()
    monkeypatch.delenv("FM_PASSWORD", raising=False)
    monkeypatch.setenv("FM_REQUIRE_AUTH", "true")
    with pytest.raises(RuntimeError, match="FM_PASSWORD"):
        require_password_configured()
    get_settings.cache_clear()

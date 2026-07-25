"""HTTP Basic Auth gate for the whole app.

This is a single-user personal tool holding real financial data, so once
it is reachable from the public internet every route must be behind a
password. The password comes from the `FM_PASSWORD` environment
variable — never committed, set per-environment.

Local development stays frictionless: if `FM_PASSWORD` is unset, auth is
disabled (and the app logs a loud warning). In any deployed environment
the variable is set, so the gate is active. `/health` is exempt so the
platform's health checks and wake-up probes still work.

Comparison uses `secrets.compare_digest` to avoid leaking the password
through response-timing differences.
"""

import logging
import secrets

from fastapi import HTTPException, Request, status
from fastapi.responses import Response

from app.config import get_settings

logger = logging.getLogger(__name__)

# Paths reachable without credentials: platform health probes only.
_PUBLIC_PATHS = {"/health"}


def _unauthorized() -> Response:
    # WWW-Authenticate makes the browser show its native login prompt.
    return Response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": 'Basic realm="Finance Monitor"'},
        content="Unauthorized",
    )


def _credentials_ok(header: str | None, expected_password: str, expected_user: str) -> bool:
    if not header or not header.lower().startswith("basic "):
        return False
    import base64
    import binascii

    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return False
    username, _, password = decoded.partition(":")
    # Both compared with compare_digest so neither leaks via timing.
    user_ok = secrets.compare_digest(username, expected_user)
    pass_ok = secrets.compare_digest(password, expected_password)
    return user_ok and pass_ok


async def basic_auth_middleware(request: Request, call_next):
    settings = get_settings()
    password = settings.password

    if not password:
        # Unset => local dev. Warn once per process, don't block.
        if not getattr(basic_auth_middleware, "_warned", False):
            logger.warning(
                "FM_PASSWORD is not set — the app is UNPROTECTED. "
                "Set it before exposing this service publicly."
            )
            basic_auth_middleware._warned = True
        return await call_next(request)

    if request.url.path in _PUBLIC_PATHS:
        return await call_next(request)

    if not _credentials_ok(request.headers.get("authorization"), password, settings.username):
        return _unauthorized()

    return await call_next(request)


def require_password_configured() -> None:
    """Fail fast at import time if a deployed environment forgot the
    password — better a crashed deploy than a public portfolio."""
    settings = get_settings()
    if settings.require_auth and not settings.password:
        raise RuntimeError(
            "FM_REQUIRE_AUTH is on but FM_PASSWORD is empty. "
            "Set FM_PASSWORD before starting."
        )


__all__ = ["basic_auth_middleware", "require_password_configured", "HTTPException"]

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import composition, holdings, portfolio, prices, simulation, transactions
from app.auth import basic_auth_middleware, require_password_configured
from app.config import get_settings

settings = get_settings()

# Refuse to start unprotected where auth is mandated (deployed envs).
require_password_configured()

app = FastAPI(title="Finance Monitor", version="0.1.0")

# Registered first so it runs outermost: nothing is served before the
# password check.
app.middleware("http")(basic_auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(holdings.router)
app.include_router(portfolio.router)
app.include_router(prices.router)
app.include_router(simulation.router)
app.include_router(transactions.router)
app.include_router(composition.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Serve the built frontend from this same process when configured, so a
# deploy needs one service instead of two. Mounted last so it never
# shadows /api/* or /health. html=True makes unknown paths fall back to
# index.html, which the SPA router needs.
if settings.static_dir:
    static_path = Path(settings.static_dir)
    if static_path.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=static_path, html=True), name="frontend")

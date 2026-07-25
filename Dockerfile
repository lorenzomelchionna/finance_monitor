# Single-service image: builds the React frontend, then serves it from
# the FastAPI process. One service instead of two keeps resident memory
# (and therefore the bill) down.

# ---- stage 1: frontend build ----
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
# --legacy-peer-deps: openapi-typescript@7 still declares a peer range of
# typescript@^5 while this project is on TS 6. It's a codegen-only dev
# tool (npm run gen:api) that works fine on 6 — the range is just stale
# upstream — but strict peer resolution makes `npm ci` refuse to install.
RUN npm ci --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# ---- stage 2: runtime ----
FROM python:3.12-slim
WORKDIR /app

# uv gives fast, lockfile-exact installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencies first so code edits don't bust the layer cache.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ ./
COPY --from=frontend /build/dist ./static

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FM_STATIC_DIR=/app/static \
    FM_DATA_DIR=/data \
    FM_REQUIRE_AUTH=true

# Migrate then serve. Running migrations at boot keeps the schema in
# step with the image without a separate release step.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

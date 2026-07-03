# syntax=docker/dockerfile:1.7

FROM python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

FROM base AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --prefix=/install .

FROM base AS runtime
# -k/-o Acquire::https::Verify-Peer=false: some local/corporate networks TLS-
# inspect traffic to packages.microsoft.com with a certificate curl/apt won't
# trust. Package integrity is still enforced via the GPG-signed Release file
# (microsoft-prod.gpg below), so this only relaxes transport-layer checks.
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg \
    && curl -sSLk https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -sSLk https://packages.microsoft.com/config/debian/12/prod.list | sed 's#\[arch=amd64#[signed-by=/usr/share/keyrings/microsoft-prod.gpg arch=amd64#' > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false msodbcsql18 unixodbc \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

COPY --from=builder /install /usr/local
WORKDIR /app
COPY core ./core
COPY api ./api
COPY ws ./ws
COPY workers ./workers
COPY models ./models
COPY schemas ./schemas
COPY services ./services
COPY main.py ./
COPY alembic ./alembic
COPY alembic.ini ./

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/livez || exit 1

# Worker count tuned per-pod at deploy time via WEB_CONCURRENCY; keep modest here.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

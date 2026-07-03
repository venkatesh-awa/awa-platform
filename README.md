# AWA Platform — Sprint 0 Scaffold

Production-ready foundation for the Al Wataneya Auction (AWA) live-auction
platform: Python FastAPI backend, Kafka + Redis event backbone, PostgreSQL,
and the supporting CI/CD, observability, and Kubernetes config. This covers
Sprint 0 from the sprint plan (`T0001`–`T0008`): repo/CI setup, cloud infra
baseline, service skeletons, auth foundation, Kafka topic design,
observability baseline, and the test frameworks.

This repo is the API/backend only. The React UI lives in the sibling
[`awa-platform-ui`](../awa-platform-ui) project and talks to this backend
over REST + WebSocket - see [Connecting the UI](#connecting-the-ui).

Every design decision here traces back to the architecture document produced
earlier in this project (dual message broker, single-writer-per-partition bid
arbitration, WebSocket fan-out via Redis pub/sub, etc.) — comments in the code
point back to the relevant section.

## Repository layout

```
core/               config, logging, database, redis, kafka, security, telemetry
api/v1/             REST endpoints (health, auctions/bids) - thin controllers only
services/           business logic - auction_service.py, bid_service.py, exceptions.py
ws/                 WebSocket gateway (per-auction rooms via Redis pub/sub)
workers/            auction_worker.py - thin Kafka consumer loop, delegates to services/
models/             SQLAlchemy ORM models
schemas/            Pydantic request/response schemas
main.py             FastAPI application factory
alembic/            database migrations
tests/              pytest suite, no real infra required (mocked)
infra/
  kafka/               topic creation script (partitioning strategy documented inline)
  k8s/                 Deployment/Service/HPA manifests for each service
  observability/       Prometheus + OpenTelemetry collector config
docker-compose.yml    local stack: Postgres, Redis, Kafka (KRaft), backend, worker
```

### Why a services layer

`api/v1/auctions.py` and `workers/auction_worker.py` both need to act on
bids, but for different reasons (one validates and publishes, the other
decides and commits). Business logic lives in `services/bid_service.py` and
`services/auction_service.py`, written without any FastAPI or Kafka-consumer
dependency — they raise plain Python exceptions from `services/exceptions.py`.
Each caller translates those into whatever error surface it needs: the API
layer maps them to HTTP status codes, the worker maps them to
retry-vs-skip decisions. This is also what makes the service functions unit
-testable without spinning up a web server or a Kafka broker (see
`tests/test_bid_service.py`).

## Quickstart (local development)

**Prerequisites:** Docker and Docker Compose.

```bash
cp .env.example .env      # adjust values if needed
docker compose up --build
```

This brings up Postgres, Redis, a single-broker Kafka cluster (topics
auto-created by `kafka-topics-init`), the backend API on `:8000`, and the
auction worker (no exposed port — consumes Kafka).

Apply database migrations once Postgres is healthy:

```bash
docker compose exec backend alembic upgrade head
```

API docs (non-production only) are at `http://localhost:8000/docs`.

## Connecting the UI

The UI is a separate project (`awa-platform-ui`) and talks to this backend
over REST (`/api/v1/...`) and WebSocket (`/ws/...`). Two ways to run it
without hitting CORS problems:

- **Local dev (recommended):** run the UI's own dev server
  (`npm run dev` in `awa-platform-ui`, default `http://localhost:5173`). Its
  Vite dev server proxies `/api` and `/ws` to this backend on `:8000`, so the
  browser only ever talks to one origin — no CORS involved at all.
- **Cross-origin (e.g. separately deployed UI):** the backend already ships
  with CORS enabled via `CORSMiddleware` (`main.py`), driven by the
  `CORS_ALLOWED_ORIGINS` env var (`.env.example` defaults it to
  `["http://localhost:5173"]`). Add the UI's real origin(s) to that list -
  it must be an explicit origin, not `*`, since `allow_credentials=True`.

## Running tests

```bash
# No real infra required, all external dependencies are mocked
pip install -e ".[dev]" && pytest
```

## What's deliberately stubbed vs. real in this scaffold

**Real and production-ready:**
- Async FastAPI app with structured logging, typed settings, health checks
  (liveness never checks dependencies, readiness always does — see
  `api/v1/health.py`), global exception handling, CORS.
- The full bid critical path: REST submission → Kafka publish (keyed by
  `auction_id`) → single-writer auction worker → Postgres commit → Redis
  cache update → Redis pub/sub → WebSocket broadcast — matching the
  architecture document exactly, including the idempotent-replay guarantee
  via the unique `(kafka_partition, kafka_offset)` index.
- JWT verification against a real OIDC JWKS endpoint (Azure B2C / UAE Pass
  compatible), with role-based access control via `require_role()`.
- Kubernetes manifests with correct probe semantics, resource requests, and
  the REST/WS-gateway/worker scaling split described in the architecture doc.
- CI pipeline: lint, format check, type check, tests, Docker build, gated on
  every PR (the UI has its own equivalent pipeline in `awa-platform-ui`).

**Deliberately stubbed — wire up in a later sprint, not Sprint 0:**
- Token *issuance* (the actual Azure B2C / UAE Pass redirect flow) — the
  UI's `AuthContext` and this repo's `security.py` both assume a token
  already exists and focus on verifying/storing it correctly.
- Deposit/buying-limit validation in `validate_bid_eligibility()` in `services/bid_service.py` — has
  the correct shape and role check (BRD R088) but needs the real deposit
  service wired in.
- The HPA on WebSocket connection count needs a custom-metrics pipeline
  (Prometheus Adapter or KEDA) not included here; falls back to CPU-based
  scaling until that's added (see comment in `ws-gateway-deployment.yaml`).
- Dead-letter topic handling for malformed Kafka messages in the auction
  worker currently logs and skips; route to a real DLQ before production.
- `infra/k8s/config.yaml` Secret values are placeholders — wire to your
  actual secrets manager (AWS Secrets Manager, Azure Key Vault, etc.) via
  the External Secrets Operator or equivalent.

## Next steps

Continue with the Sprint 1 backlog from the sprint plan (User Management &
Registration, Vehicle Listing & Yard Management) using this scaffold's
patterns: add new routers under `api/v1/`, new service modules under `services/`, new models under
`models/`, and follow the same test-with-mocked-infra approach.

"""FastAPI application entrypoint.

Run locally with: uvicorn main:app --reload
Run in production with: uvicorn main:app --host 0.0.0.0 --port 8000 --workers N
(see Dockerfile CMD - workers count is tuned per-pod via k8s resource requests)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from api.v1.router import api_router
from core.config import get_settings
from core.database import dispose_engine, init_engine
from core.kafka import dispose_kafka_producer, init_kafka_producer
from core.logging import configure_logging, get_logger
from core.redis import dispose_redis, init_redis
from core.telemetry import configure_tracing
from ws.gateway import router as ws_router

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("app_starting", environment=settings.environment)

    init_engine()
    init_redis()
    await init_kafka_producer()

    yield

    logger.info("app_shutting_down")
    await dispose_kafka_producer()
    await dispose_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Pydantic error dicts can carry non-JSON-native values in `ctx` (e.g.
        # Decimal for a `gt=0` constraint) - jsonable_encoder converts those,
        # where a raw json.dumps of exc.errors() would blow up into a 500.
        errors = jsonable_encoder(exc.errors())
        logger.warning("request_validation_failed", path=str(request.url), errors=errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Invalid request", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=str(request.url))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(ws_router)

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount(settings.upload_base_url, StaticFiles(directory=upload_path), name="uploads")

    configure_tracing(app)
    Instrumentator().instrument(app).expose(app, endpoint=settings.prometheus_metrics_path)

    return app


app = create_app()

"""OpenTelemetry tracing setup. Exports spans via OTLP to the collector
configured in infra/observability (see architecture doc Section 13).
Metrics are handled separately by prometheus-fastapi-instrumentator in main.py.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


def configure_tracing(app) -> None:  # noqa: ANN001 - FastAPI app instance
    settings = get_settings()

    if not settings.otel_exporter_otlp_endpoint:
        logger.info("otel_tracing_disabled_no_endpoint_configured")
        return

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    logger.info("otel_tracing_configured", endpoint=settings.otel_exporter_otlp_endpoint)


def get_tracer(name: str):  # noqa: ANN201
    return trace.get_tracer(name)

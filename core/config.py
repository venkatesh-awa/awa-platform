"""Centralized, typed application configuration.

All configuration is sourced from environment variables (or a local .env file
during development) and validated at startup via Pydantic. The app must fail
fast on misconfiguration rather than surface obscure errors at request time.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    environment: str = Field(default="local", pattern="^(local|dev|staging|production)$")
    app_name: str = "awa-backend"
    log_level: str = "INFO"
    log_json: bool = False

    # --- API ---
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: list[str] = Field(default_factory=list)

    # --- Database ---
    database_url: PostgresDsn
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # --- Redis ---
    redis_url: RedisDsn

    # --- Kafka ---
    kafka_bootstrap_servers: str
    kafka_consumer_group: str = "awa-auction-workers"
    kafka_topic_bids: str = "auction.bids"
    kafka_topic_bid_results: str = "auction.bid_results"

    # --- Auth ---
    auth_issuer: str
    auth_audience: str
    auth_jwks_url: str
    auth_jwt_algorithms: list[str] = Field(default_factory=lambda: ["RS256"])

    # --- Observability ---
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "awa-backend"
    prometheus_metrics_path: str = "/metrics"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got {v!r}")
        return upper

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Import and call this, never instantiate Settings() directly."""
    return Settings()  # type: ignore[call-arg]

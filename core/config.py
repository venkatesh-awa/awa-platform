"""Centralized, typed application configuration.

All configuration is sourced from environment variables (or a local .env file
during development) and validated at startup via Pydantic. The app must fail
fast on misconfiguration rather than surface obscure errors at request time.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder used as the JWT signing secret when none is supplied. Fine for
# local/dev; rejected at startup in production (see _validate_prod_secrets).
_DEV_JWT_SECRET = "dev-insecure-change-me"  # noqa: S105 - not a real credential


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
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    database_echo: bool = False

    # --- Redis ---
    redis_url: RedisDsn

    # --- Kafka ---
    kafka_bootstrap_servers: str
    kafka_consumer_group: str = "awa-auction-workers"
    kafka_topic_bids: str = "auction.bids"
    kafka_topic_bid_results: str = "auction.bid_results"

    # --- Auth: external IdP token verification (Azure B2C / UAE Pass) ---
    auth_issuer: str
    auth_audience: str
    auth_jwks_url: str
    auth_jwt_algorithms: list[str] = Field(default_factory=lambda: ["RS256"])

    # --- Auth: local email/password (sign up / sign in / password reset) ---
    # HS256 secret used to sign the access tokens THIS service issues (distinct
    # from the external-IdP tokens verified above). Must be overridden in prod.
    auth_jwt_secret: str = _DEV_JWT_SECRET
    auth_local_issuer: str = "awa-backend"
    # Access token: short-lived JWT. Refresh token: long-lived opaque token,
    # stored hashed and rotated on use. Reset/verify tokens: single-use, hashed.
    auth_access_token_ttl_seconds: int = 900  # 15 minutes
    auth_refresh_token_ttl_seconds: int = 2_592_000  # 30 days
    auth_password_reset_ttl_seconds: int = 3_600  # 1 hour
    auth_email_verification_ttl_seconds: int = 86_400  # 24 hours
    # Brute-force protection: lock the account for a window after N failures.
    auth_max_failed_logins: int = 5
    auth_lockout_seconds: int = 900  # 15 minutes
    # Base URL of the web app, used to build password-reset / verify links.
    frontend_base_url: str = "http://localhost:5173"

    # --- File uploads (seller document intake, e.g. Mulkhiya) ---
    # Local disk storage for now - no S3/Blob wired up in this service yet.
    # /tmp is writable by the non-root container user (see Dockerfile's
    # appuser, which doesn't own /app); mount a volume there for persistence.
    upload_dir: str = "/tmp/uploads"
    upload_base_url: str = "/static/uploads"

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

    @model_validator(mode="after")
    def _validate_prod_secrets(self) -> Settings:
        # Fail fast rather than silently sign production tokens with a known
        # placeholder secret (which would let anyone forge access tokens).
        if self.environment == "production" and self.auth_jwt_secret == _DEV_JWT_SECRET:
            raise ValueError("AUTH_JWT_SECRET must be set to a strong value in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Import and call this, never instantiate Settings() directly."""
    return Settings()  # type: ignore[call-arg]

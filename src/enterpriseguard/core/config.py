"""
EnterpriseGuard
Core Configuration Module

This module provides validated application configuration
for development, testing, staging, and production environments.

Security principles:
- Never hard-code secrets.
- Never expose secrets through configuration serialization.
- Fail fast when required production configuration is missing.
- Keep environment-specific configuration outside application code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


APPLICATION_NAME: Final[str] = "EnterpriseGuard"
APPLICATION_VERSION: Final[str] = "4.0.0"


class ConfigurationError(RuntimeError):
    """Raised when the application configuration is invalid."""


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable safely."""

    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ConfigurationError(
        f"Environment variable '{name}' must be a boolean value."
    )


def _get_int(
    name: str,
    default: int,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Read and validate an integer environment variable."""

    value = os.getenv(name)

    if value is None:
        result = default
    else:
        try:
            result = int(value)
        except ValueError as exc:
            raise ConfigurationError(
                f"Environment variable '{name}' must be an integer."
            ) from exc

    if minimum is not None and result < minimum:
        raise ConfigurationError(
            f"Environment variable '{name}' must be >= {minimum}."
        )

    if maximum is not None and result > maximum:
        raise ConfigurationError(
            f"Environment variable '{name}' must be <= {maximum}."
        )

    return result


def _get_required(name: str) -> str:
    """Read a required environment variable."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise ConfigurationError(
            f"Required environment variable '{name}' is missing."
        )

    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Immutable application settings.

    Secrets are intentionally not given unsafe fallback values.
    Production deployments must provide them explicitly.
    """

    app_name: str = APPLICATION_NAME
    version: str = APPLICATION_VERSION

    environment: str = os.getenv(
        "ENTERPRISEGUARD_ENV",
        "development",
    ).strip().lower()

    debug: bool = _get_bool("ENTERPRISEGUARD_DEBUG", False)

    host: str = os.getenv(
        "ENTERPRISEGUARD_HOST",
        "127.0.0.1",
    )

    port: int = _get_int(
        "ENTERPRISEGUARD_PORT",
        5000,
        minimum=1,
        maximum=65535,
    )

    database_url: str = os.getenv(
        "ENTERPRISEGUARD_DATABASE_URL",
        "sqlite:///enterpriseguard.db",
    )

    redis_url: str = os.getenv(
        "ENTERPRISEGUARD_REDIS_URL",
        "redis://localhost:6379/0",
    )

    jwt_algorithm: str = os.getenv(
        "ENTERPRISEGUARD_JWT_ALGORITHM",
        "HS256",
    )

    jwt_expiration_minutes: int = _get_int(
        "ENTERPRISEGUARD_JWT_EXPIRATION_MINUTES",
        15,
        minimum=1,
        maximum=1440,
    )

    refresh_token_expiration_days: int = _get_int(
        "ENTERPRISEGUARD_REFRESH_TOKEN_EXPIRATION_DAYS",
        30,
        minimum=1,
        maximum=365,
    )

    rate_limit_per_minute: int = _get_int(
        "ENTERPRISEGUARD_RATE_LIMIT_PER_MINUTE",
        60,
        minimum=1,
        maximum=10000,
    )

    audit_logging_enabled: bool = _get_bool(
        "ENTERPRISEGUARD_AUDIT_LOGGING",
        True,
    )

    metrics_enabled: bool = _get_bool(
        "ENTERPRISEGUARD_METRICS",
        True,
    )

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""

        return self.environment == "production"

    def validate(self) -> None:
        """
        Validate settings that depend on the selected environment.

        Development intentionally uses safe local defaults.
        Production requires explicit cryptographic secrets.
        """

        allowed_environments = {
            "development",
            "testing",
            "staging",
            "production",
        }

        if self.environment not in allowed_environments:
            raise ConfigurationError(
                "ENTERPRISEGUARD_ENV must be one of: "
                + ", ".join(sorted(allowed_environments))
            )

        if self.is_production:
            secret_key = os.getenv("ENTERPRISEGUARD_SECRET_KEY")
            refresh_secret = os.getenv(
                "ENTERPRISEGUARD_REFRESH_SECRET_KEY"
            )

            if not secret_key:
                raise ConfigurationError(
                    "ENTERPRISEGUARD_SECRET_KEY is required in production."
                )

            if not refresh_secret:
                raise ConfigurationError(
                    "ENTERPRISEGUARD_REFRESH_SECRET_KEY "
                    "is required in production."
                )

            if len(secret_key) < 32:
                raise ConfigurationError(
                    "ENTERPRISEGUARD_SECRET_KEY must contain "
                    "at least 32 characters."
                )

            if len(refresh_secret) < 32:
                raise ConfigurationError(
                    "ENTERPRISEGUARD_REFRESH_SECRET_KEY must contain "
                    "at least 32 characters."
                )

            if self.debug:
                raise ConfigurationError(
                    "Debug mode must be disabled in production."
                )

    def public_dict(self) -> dict[str, object]:
        """
        Return configuration safe for diagnostics/API responses.

        Secrets are never returned.
        """

        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "database_configured": bool(self.database_url),
            "redis_configured": bool(self.redis_url),
            "jwt_algorithm": self.jwt_algorithm,
            "jwt_expiration_minutes": self.jwt_expiration_minutes,
            "refresh_token_expiration_days": (
                self.refresh_token_expiration_days
            ),
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "audit_logging_enabled": self.audit_logging_enabled,
            "metrics_enabled": self.metrics_enabled,
        }


settings = Settings()
settings.validate()
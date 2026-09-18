"""HTTP API package.

Endpoints:
- GET  /v1/health    (public)
- POST /v1/decisions (auth required)
- POST /v1/verify    (auth required)

See continuity/DC-140_HTTP_API_DESIGN.md for design rationale.
"""

from .server import (
    APIError,
    DEFAULT_HOST,
    DEFAULT_PORT,
    create_server,
)

__all__ = [
    "APIError",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "create_server",
]

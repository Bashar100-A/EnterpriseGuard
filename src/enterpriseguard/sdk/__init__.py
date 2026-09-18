"""SDK integration layer.

Single entry point for creating and signing decisions.
See continuity/DC-139_SDK_CLIENT_DESIGN.md for design rationale.
"""

from .client import (
    Client,
    SignedDecision,
    SDKError,
)

__all__ = [
    "Client",
    "SignedDecision",
    "SDKError",
]

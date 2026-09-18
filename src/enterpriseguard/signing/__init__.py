"""SDK signing module.

Independent from tools/signing_backend.py by design.
See continuity/DC-137_SDK_SIGNING_MODULE.md for rationale.
"""

from .backend import (
    DEFAULT_KEY_DIR,
    SUPPORTED_BACKENDS,
    SigningError,
    SigningKeyInvalidError,
    SigningKeyNotFoundError,
    sign_bytes,
    verify_signature_hex,
)

__all__ = [
    "DEFAULT_KEY_DIR",
    "SUPPORTED_BACKENDS",
    "SigningError",
    "SigningKeyInvalidError",
    "SigningKeyNotFoundError",
    "sign_bytes",
    "verify_signature_hex",
]

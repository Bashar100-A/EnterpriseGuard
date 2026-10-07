"""Canonical Trust Status & Revocation (Stage 3C)."""
from .status import TrustStatus, TERMINAL, REVERSIBLE
from .authority_to_revoke import (
    RevocationAuthority, RevocationKind,
    RevocationAuthorityError, RevocationAuthorityValidationError,
    RevocationNotPermittedError,
)
from .assertion import (
    TrustStatusAssertion, TrustStatusAssertionError,
    TrustStatusAssertionValidationError,
)
from .resolver import (
    TrustStatusResolver, ResolutionOutcome, ResolvedStatus,
)
from .history import (
    TrustStatusStore, TrustHistoryError, TrustHistoryIntegrityError,
)

__all__ = [
    "TrustStatus", "TERMINAL", "REVERSIBLE",
    "RevocationAuthority", "RevocationKind",
    "RevocationAuthorityError", "RevocationAuthorityValidationError",
    "RevocationNotPermittedError",
    "TrustStatusAssertion", "TrustStatusAssertionError",
    "TrustStatusAssertionValidationError",
    "TrustStatusResolver", "ResolutionOutcome", "ResolvedStatus",
    "TrustStatusStore", "TrustHistoryError", "TrustHistoryIntegrityError",
]

"""One-directional adapter: legacy DecisionContract (B) -> canonical (A).

Legacy B surface:  enterpriseguard.decision.contracts.DecisionContract
Canonical A:       enterpriseguard.adie.decision.DecisionContract

B is LEGACY / COMPATIBILITY. It MUST NOT independently authorize.

The adapter translates B into a neutral dict that the canonical
governance path can consume. It does NOT create authority from B.
"""
from __future__ import annotations

from typing import Any

from .lifecycle import AuthorizationStatus, DecisionLifecycle


_LEGACY_STATUS_MAP: dict[str, AuthorizationStatus] = {
    "pending": AuthorizationStatus.PENDING,
    "authorized": AuthorizationStatus.AUTHORIZED,
    "denied": AuthorizationStatus.DENIED,
    "expired": AuthorizationStatus.EXPIRED,
    "superseded": AuthorizationStatus.SUPERSEDED,
}


class LegacyAdapterError(ValueError):
    pass


def legacy_status_to_authorization(legacy_status_value: str) -> AuthorizationStatus:
    """Map a legacy B DecisionStatus value to the authorization axis.

    Legacy B's DecisionStatus was conflating authorization and validity.
    SUPERSEDED and EXPIRED are validity states in B; we keep them on the
    authorization axis here because Stage 3B defines a single authorization
    axis. (If a distinct validity axis is later required, this mapping
    will be revisited.)
    """
    v = str(legacy_status_value).strip().lower()
    if v not in _LEGACY_STATUS_MAP:
        raise LegacyAdapterError(f"unknown legacy status: {legacy_status_value!r}")
    return _LEGACY_STATUS_MAP[v]


def legacy_contract_to_neutral(legacy: Any) -> dict:
    """Extract neutral fields from a legacy B DecisionContract.

    Returns a dict; does NOT construct authority. Caller must supply
    explicit Authority if authorization is required.
    """
    if not hasattr(legacy, "status") or not hasattr(legacy, "authorized"):
        raise LegacyAdapterError("object does not look like legacy DecisionContract")

    auth = legacy_status_to_authorization(getattr(legacy.status, "value", str(legacy.status)))

    return {
        "legacy_decision_id": getattr(legacy, "decision_id", None),
        "evaluation_id": getattr(legacy, "evaluation_id", None),
        "policy_id": getattr(legacy, "policy_id", None),
        "authorization_status": auth,
        # NOTE: we deliberately do NOT project the legacy `authorized` bool
        # onto the canonical authorization axis. Legacy's bool is not an
        # Authority; it's a claim. The canonical path requires explicit
        # Authority validation before authorizing.
        "legacy_authorized_claim": bool(getattr(legacy, "authorized", False)),
        "target_resource_id": getattr(legacy, "target_resource_id", None),
        "expires_at": getattr(legacy, "expires_at", None),
    }


__all__ = [
    "LegacyAdapterError",
    "legacy_status_to_authorization",
    "legacy_contract_to_neutral",
]

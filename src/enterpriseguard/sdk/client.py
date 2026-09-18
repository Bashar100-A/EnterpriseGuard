#!/usr/bin/env python3
"""SDK Client — single entry point for decisions + signing.

Wraps:
- enterpriseguard.decision.contracts (DecisionContract)
- enterpriseguard.signing (sign_bytes, verify_signature_hex)

Design: continuity/DC-139_SDK_CLIENT_DESIGN.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from enterpriseguard.decision.contracts import (
    ADIEDecision,
    DecisionContract,
    DecisionValidationError,
)
from enterpriseguard.signing import (
    DEFAULT_KEY_DIR,
    SUPPORTED_BACKENDS,
    sign_bytes,
    verify_signature_hex,
)


class SDKError(RuntimeError):
    """Base exception for SDK Client errors."""


class _PolicyEvaluationAdapter:
    """Internal duck-typed adapter for ADIEDecision.evaluate_policy_result."""

    def __init__(
        self,
        *,
        evaluation_id: str,
        policy_id: str,
        intent: str,
        allowed: bool,
        decision_score: float = 1.0,
    ) -> None:
        self.evaluation_id = evaluation_id
        self.policy_id = policy_id
        self.intent = intent
        self.allowed = allowed
        self.decision_score = decision_score


def _derive_evaluation_id(
    target: str,
    intent: str,
    policy_id: str,
    parameters: Mapping[str, Any] | None,
) -> str:
    """Deterministic evaluation_id derived from inputs (reproducibility)."""
    payload = {
        "target": target,
        "intent": intent,
        "policy_id": policy_id,
        "parameters": dict(parameters) if parameters else {},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return f"eval-{digest[:32]}"


def _derive_decision_id(
    evaluation_id: str,
    action_value: str,
    policy_id: str,
    target: str,
) -> str:
    """Deterministic decision_id derived from contract inputs.

    Overrides the engine-internal counter-based ID so the SDK surface
    is reproducible (same inputs -> same decision_id).
    """
    payload = {
        "evaluation_id": evaluation_id,
        "action": action_value,
        "policy_id": policy_id,
        "target": target,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return f"dec-{digest[:24]}"


def _canonical_payload(contract: DecisionContract, signed_at: datetime) -> str:
    """Exact string covered by the signature.

    Includes signed_at so that tampering with the signing timestamp
    invalidates verification.
    """
    payload = {
        "contract": contract.to_dict(),
        "signed_at": signed_at.astimezone(timezone.utc).isoformat(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class SignedDecision:
    """A DecisionContract plus its detached signature (composition)."""

    contract: DecisionContract
    signature_hex: str
    signed_at: datetime
    backend: str
    signed_payload_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract.to_dict(),
            "signature_hex": self.signature_hex,
            "signed_at": self.signed_at.astimezone(timezone.utc).isoformat(),
            "backend": self.backend,
            "signed_payload_hash": self.signed_payload_hash,
        }


class Client:
    """SDK Client.

    5-line usage:

        from enterpriseguard.sdk import Client

        client = Client()
        signed = client.decide(target="host-01", intent="isolate")
        assert client.verify(signed)
    """

    def __init__(
        self,
        *,
        key_dir: Path | None = None,
        backend: str = "rsa_local",
    ) -> None:
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"Unsupported backend: {backend}")
        self._key_dir = key_dir if key_dir is not None else DEFAULT_KEY_DIR
        self._backend = backend
        self._engine = ADIEDecision()

    # ─────────────────── primitives ───────────────────

    def create_decision(
        self,
        *,
        target: str,
        intent: str,
        allowed: bool = True,
        policy_id: str = "default",
        evaluation_id: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> DecisionContract:
        """Create (but do not sign) a DecisionContract.

        If evaluation_id is omitted, it is derived deterministically from
        (target, intent, policy_id, parameters) so the same inputs always
        produce the same decision_id.
        """
        if evaluation_id is None:
            evaluation_id = _derive_evaluation_id(
                target, intent, policy_id, parameters
            )

        adapter = _PolicyEvaluationAdapter(
            evaluation_id=evaluation_id,
            policy_id=policy_id,
            intent=intent,
            allowed=allowed,
        )
        try:
            contract = self._engine.evaluate_policy_result(
                policy_evaluation=adapter,
                target_resource_id=target,
                extra_parameters=parameters,
            )
        except DecisionValidationError as exc:
            raise SDKError(f"Decision creation failed: {exc}") from exc

        # Override the engine's counter-based decision_id with a
        # deterministic one. Reset provenance_hash so it is recomputed
        # over the new decision_id.
        det_id = _derive_decision_id(
            contract.evaluation_id,
            contract.action.value,
            policy_id,
            target,
        )
        return replace(contract, decision_id=det_id, provenance_hash="")

    def sign(self, contract: DecisionContract) -> SignedDecision:
        """Sign a DecisionContract; return a SignedDecision."""
        signed_at = datetime.now(timezone.utc)
        payload = _canonical_payload(contract, signed_at)
        signature_hex = sign_bytes(
            payload,
            backend=self._backend,
            key_dir=self._key_dir,
        )
        payload_hash = sha256(payload.encode("utf-8")).hexdigest()

        return SignedDecision(
            contract=contract,
            signature_hex=signature_hex,
            signed_at=signed_at,
            backend=self._backend,
            signed_payload_hash=payload_hash,
        )

    def verify(self, signed: SignedDecision) -> bool:
        """Verify a SignedDecision. Returns False on any failure."""
        if not isinstance(signed, SignedDecision):
            return False

        try:
            payload = _canonical_payload(signed.contract, signed.signed_at)
        except Exception:
            return False

        expected_hash = sha256(payload.encode("utf-8")).hexdigest()
        if expected_hash != signed.signed_payload_hash:
            return False

        try:
            return verify_signature_hex(
                payload,
                signed.signature_hex,
                backend=signed.backend,
                key_dir=self._key_dir,
            )
        except Exception:
            return False

    # ─────────────────── convenience ───────────────────

    def decide(
        self,
        *,
        target: str,
        intent: str,
        allowed: bool = True,
        policy_id: str = "default",
        evaluation_id: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> SignedDecision:
        """create_decision(...) + sign(...) in one call."""
        contract = self.create_decision(
            target=target,
            intent=intent,
            allowed=allowed,
            policy_id=policy_id,
            evaluation_id=evaluation_id,
            parameters=parameters,
        )
        return self.sign(contract)

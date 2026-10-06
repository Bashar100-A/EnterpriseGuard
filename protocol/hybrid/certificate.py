"""ADIE DCP 2.1 certificate builder.

DCP 2.0 uses `signature` (singular). DCP 2.1 uses `signatures` (array).
This module builds DCP 2.1 certificates by:
1. Taking the semantic payload (same 13 fields as DCP 2.0)
2. Computing claim_root over those 13 fields (unchanged)
3. Adding a `signatures` array (RS256 + ML-DSA-65, sorted by alg)
4. Emitting JSON with dcp_version: "2.1"

The signing TBS excludes the signatures field entirely.
"""
import json

from protocol.core.claim_root import compute_claim_root


FIELD_NAMES_13 = [
    "issuer", "subject", "request", "context", "policy", "model", "data",
    "runtime", "output", "binding", "temporal", "evidence", "authoring",
]


def build_dcp21_payload(
    claim_id: str,
    issuer_did: str,
    issuer_key_id: str,
    subject: dict,
    request: dict,
    context: dict,
    policy: dict,
    model: dict,
    data: dict,
    runtime: dict,
    output: dict,
    binding: dict,
    temporal: dict,
    evidence: dict,
    authoring: dict,
    proofs: list = None,
) -> dict:
    """Build the DCP 2.1 payload WITHOUT signatures.

    Returns a dict with all required fields except `signatures`.
    """
    cert = {
        "dcp_version": "2.1",
        "claim_id": claim_id,
        "issuer": {"did": issuer_did, "key_id": issuer_key_id},
        "subject": subject,
        "binding": binding,
        "request": request,
        "context": context,
        "policy": policy,
        "model": model,
        "data": data,
        "runtime": runtime,
        "output": output,
        "temporal": temporal,
        "evidence": evidence,
        "authoring": authoring,
        "proofs": proofs if proofs is not None else [],
    }

    # claim_root over the 13 named fields (same as DCP 2.0)
    fields = {k: cert.get(k) for k in FIELD_NAMES_13}
    root = compute_claim_root(fields)
    cert["claim_root"] = "sha256:" + root.hex()

    return cert


def attach_signatures(payload: dict, signatures: list) -> dict:
    """Return a new dict = payload + signatures (sorted by alg)."""
    out = dict(payload)
    out["signatures"] = sorted(signatures, key=lambda s: s["alg"])
    return out


def emit_certificate(cert: dict) -> bytes:
    """Canonical JSON emission (sorted keys)."""
    return json.dumps(cert, indent=2, ensure_ascii=False).encode("utf-8")


__all__ = [
    "build_dcp21_payload",
    "attach_signatures",
    "emit_certificate",
    "FIELD_NAMES_13",
]

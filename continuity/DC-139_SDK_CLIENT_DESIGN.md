# DC-139: SDK Client Design (B1.11)

**Date:** 2026-09-18
**Owner:** Biss
**Status:** APPROVED
**Related:** DC-137 (signing module), DC-138 (defer top-level)

## Context

Phase B target: "Create a decision in <=5 lines of Python."

Today we have:
- src/enterpriseguard/decision/contracts.py: ADIEDecision + DecisionContract
- src/enterpriseguard/signing/: sign_bytes + verify_signature_hex
- No integration layer between the two domains.

## Goal

Add src/enterpriseguard/sdk/ providing a single Client class with a
minimal, clear API.

## Proposed API (target: 5 lines)

    from enterpriseguard.sdk import Client

    client = Client()
    signed = client.decide(target="host-01", intent="isolate")
    assert client.verify(signed)

## Design Decisions (to be approved)

### D1. Location
    src/enterpriseguard/sdk/
        __init__.py    (re-exports Client, SignedDecision)
        client.py      (implementation)

### D2. Client constructor
    Client(key_dir: Path | None = None, backend: str = "rsa_local")

Same defaults as signing module. No env var reads.

### D3. create_decision
    def create_decision(
        self,
        *,
        target: str,
        intent: str,
        allowed: bool = True,
        policy_id: str = "default",
        evaluation_id: str | None = None,
        parameters: dict | None = None,
    ) -> DecisionContract

Wraps ADIEDecision.evaluate_policy_result using a minimal internal
adapter object (duck-typed to satisfy evaluate_policy_result). No new
PolicyEvaluation class is introduced; the adapter lives inside client.py.

### D4. sign
    def sign(self, contract: DecisionContract) -> SignedDecision

SignedDecision = frozen dataclass:
    - contract: DecisionContract
    - signature_hex: str
    - signed_at: datetime (UTC)
    - backend: str
    - signed_payload_hash: str  # sha256 of contract.provenance_hash

Signing signs the contract's canonical to_dict() JSON (sorted keys).
A SignedDecision.to_dict() exists for serialization.

### D5. verify
    def verify(self, signed: SignedDecision) -> bool

Recomputes the canonical payload, checks the contract hash matches,
then calls verify_signature_hex. Returns False (never raises) on any
mismatch.

### D6. decide (convenience)
    def decide(self, *, target: str, intent: str, **kwargs) -> SignedDecision

Shorthand: create_decision(...) + sign(...).

### D7. Non-goals
- No network calls.
- No storage persistence (that is B1.12 or later).
- No policy engine (policy is passed as intent string).
- No TSA integration.
- No KMS.

## Why this shape

- decision/ stays focused on contracts.
- signing/ stays focused on crypto.
- sdk/ is the only integration surface.
- Client is the single entry point documented in Phase A docs.

## Consequences

- New package: enterpriseguard.sdk + enterpriseguard.sdk.*
- pyproject.toml include list extended.
- VERSION: 0.3.0 -> 0.4.0.
- tests/test_sdk_client.py with >=5 scenarios.

## Verification plan

1. 5-line example runs end-to-end.
2. Sign -> verify round-trip passes.
3. Tampered contract -> verify returns False.
4. Missing key -> SigningKeyNotFoundError propagates.
5. decide() returns SignedDecision with expected fields.
6. All existing tests still pass (no regression in decision/ or signing/).

## Rollback

Single commit. git revert if needed.

## Open questions for owner review

Q1. Is "sdk" the right folder name, or should this live at
    src/enterpriseguard/client/?

Q2. Should SignedDecision wrap the contract (composition) or should
    the signature live directly on DecisionContract (contract change)?
    Proposed: composition (no change to DecisionContract).

Q3. Should decide() be the only public entry, or keep both
    create_decision + sign + decide?

Q4. Is VERSION 0.4.0 correct, or should this wait until a fuller SDK
    exists?

## Owner Decisions (2026-09-18)

- Q1: folder name = `sdk` (not `client`)
- Q2: composition (SignedDecision wraps DecisionContract; no contract change)
- Q3: keep all three — create_decision, sign, decide
- Q4: VERSION 0.3.0 -> 0.4.0

**Approved by:** Biss (Owner)
**Effective:** 2026-09-18

# ADIE POC — Independent Verifier

**Phase:** P-STEP-02
**Protocol:** DCP Profile 1
**Verifier version:** 1.0

## What is this?

A proof-of-concept demonstrating that an independent party can verify
a decision certificate's integrity without trusting the issuing system.

## What this proves

- An external verifier can validate a certificate offline, with
  no network, no ADIE package, and no trust in the issuer's runtime.
- Tampering is detected with a deterministic error code (E001-E010).
- The verifier is 179 lines and can be read in 10 minutes.

## What this does NOT prove

- That the decision actually occurred.
- That the AI model computed correctly.
- That the inputs were accurate.
- Anything about causal sufficiency.

**Integrity != Truth.** This POC tests Integrity only.

## Quick test (5 minutes)

### Prerequisites

    pip install cryptography jcs

### Test 1 - Valid certificate

    python3 verify.py certificate-001.json public-key-001.pem
    # Expected output: VALID

### Test 2 - Wrong public key

    python3 verify.py certificate-001.json wrong-key.pem
    # Expected output: INVALID: E001_SIGNATURE_INVALID

### Test 3 - Full suite (10 cases)

    python3 test_pstep02.py
    # Expected output: Results: 10/10 passed

## Files

| File | Purpose |
|---|---|
| verify.py | Standalone verifier (179 lines, no enterpriseguard import) |
| certificate-001.json | Signed decision certificate (test fixture) |
| public-key-001.pem | Correct public key |
| wrong-key.pem | Deliberately incorrect key (for TC-09) |
| private-key-001.pem | Signing key (POC only; not for distribution) |
| test_pstep02.py | Automated test suite (10 cases) |

## Error Codes

| Code | Meaning |
|---|---|
| E001_SIGNATURE_INVALID | Signature does not verify, or wrong key |
| E002_HASH_MISMATCH | Content hash or fingerprint doesn't match |
| E003_SCHEMA_VIOLATION | Missing or malformed field |
| E004_JCS_MISMATCH | Canonicalization failed |
| E005_ALG_UNSUPPORTED | Signature or fingerprint algorithm unknown |
| E006_TIMESTAMP_INVALID | Timestamp format invalid |
| E007_VERSION_MISMATCH | Protocol version not supported |
| E008_REPLAY_OR_EXPIRED | Certificate outside validity window |
| E009_UNICODE_INVALID | Invalid Unicode in a string field |
| E010_JSON_DUPLICATE_KEY | Duplicate key in JSON object |

## Trust Boundaries

**Trusted:**
- SHA-256
- RSA-2048 PKCS#1 v1.5 with SHA-256
- The public key (delivered out-of-band)

**NOT trusted:**
- The issuing system after issuance
- Any network or database
- The verifier's own environment beyond the cryptography library

## What to Inspect First

If you are a security reviewer, focus on:

1. verify.py - 179 lines, no hidden imports.
2. Canonicalization path: uses jcs (RFC 8785), not json.dumps.
3. Signature path: signs over emission_fingerprint (RFC 6962 Merkle
   root), not over the raw JSON directly.

## Independent Test Checklist

A non-ADIE developer should be able to:

- [ ] Install dependencies (cryptography, jcs)
- [ ] Run verify.py and see VALID
- [ ] Read the 179 lines and understand the flow
- [ ] Confirm no network access is used
- [ ] Confirm no enterpriseguard import exists

If any of the above is not possible in 10 minutes, this README has failed.


## Tested Environments

| OS | Python | cryptography | jcs | Result |
|---|---|---|---|---|
| Ubuntu 22.04+ | 3.12 | 41.0.7 | 0.2.1 | 10/10 passed (rehearsal, 2026-10-04) |

**Note:** The rehearsal above was performed by the project owner,
not an external developer. It confirms the environment works but
does NOT constitute Gate 2 evidence.

**Untested (but expected to work):** macOS, Windows, Python 3.11, 3.13.

**Reported issues:** None as of 2026-10-04.

## License

TBD (likely MIT or Apache-2.0; decided in Phase B).

## Feedback

This POC is under external review. If you find a case where the verifier
accepts an invalid certificate, that is a critical finding. Please report it.

**End of README.**

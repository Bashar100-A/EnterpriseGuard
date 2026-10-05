# Gate 2 Windows Finding — 2026-10-04

## Tester
Environment: Windows 11, Python 3.12
Relationship: Institutional contact (not the owner)

## Reported Results (verbatim)

- Test A: INVALID: E002_HASH_MISMATCH
- Test B: INVALID: E001_SIGNATURE_INVALID
- Test C: 2/10 passed
- Verbatim error: INVALID: E002_HASH_MISMATCH (content_hash)

## Their Diagnosis

"Windows environment converted the line endings of certificate-001.json
from LF to CRLF upon extraction, which completely broke the canonical
JCS hashing logic."

## Our Analysis

Partially confirmed. JCS operates on parsed objects, not raw bytes,
so pure CRLF in JSON should not have broken hashing. But the fix
(raw-byte reading + BOM stripping + explicit UTF-8 decode) makes the
verifier OS-agnostic regardless of the exact mechanism.

## Fix Deployed

POC v3 (adie-external-test-v3-20261004.tar.gz).

## Retest Status

Pending.


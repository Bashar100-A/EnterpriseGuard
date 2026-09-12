# Lost GPG Key Archive

**Archived:** 2026-09-12
**Reason:** The GPG signing key that produced these signatures was lost.

## Key Details (from DC-041)

- **UID:** `EnterpriseGuard ADIE <adie@enterpriseguard.local>`
- **Algorithm:** RSA 4096 (sign only)
- **Long Key ID:** `9188569AD7F609C869730CFB20AB83C64E6B50CB`
- **Creation date:** 2026-09-01
- **Loss date:** 2026-09-12
- **Loss cause:** Original OS user `bashar` and `/home/bashar/.gnupg/` were destroyed by OS reformat.
- **Backup status:** No backup existed.

## Signature Status

The following `.asc` files are **NO LONGER VERIFIABLE**:

| File | Original Location |
|------|------------------|
| VERSION.asc | repository root |
| CHANGELOG.md.asc | repository root |
| TRUSTED_BASELINE_SENTINEL.json.asc | repository root |
| integrity_baseline_sentinel.json.asc | repository root |
| tools/TRUSTED_BASELINE.json.asc | tools/ |
| tools/integrity_baseline.json.asc | tools/ |

## Governance Lessons (DC-041 Retrospective)

Three systematic failures occurred:

1. **Full fingerprint was never recorded** in any project file.
2. **No backup of the private key** existed outside the host machine.
3. **Public key was never exported** to a persistent location.

## Remediation

These files are preserved for audit trail only. They MUST NOT be used for verification.
A new key will be generated with proper backup and documentation practices.

See: `DC-<pending>` in `tools/DECISIONS_LOG.md` and `BLOCKER-004`.

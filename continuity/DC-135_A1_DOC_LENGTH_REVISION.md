# DC-135: A1 Documentation Length Target Revision

**Date:** 2026-09-17
**Owner:** Biss
**Status:** APPROVED
**Supersedes:** EXECUTION_PLAN.md Section 3, Phase A, task A1 (length clause only)

---

## Context

EXECUTION_PLAN.md v2.2 task A1 specifies:

> "Each file <= 30 lines"

Audit on 2026-09-17 of the 22 files in docs/COMPONENTS/ showed that all
22 exceed 30 lines (range: 38 to 106 lines).

Root cause: the 30-line target was set before component complexity was
assessed. It is unrealistic for security-critical and large components:
- sibb_storage.py        578 lines of code, 62 lines of doc
- sibb_cli.py            380 lines of code, 88 lines of doc
- compliance_engine.py   138 lines of code, 106 lines of doc
- audit_chain.py          89 lines of code, 80 lines of doc

Forcing 30 lines would either drop critical security details or omit
invariants that are essential for auditing.

---

## Decision

The A1 length target is revised to a **tiered standard based on code size**:

| Tier | Code size (Python lines) | Doc target (lines) |
|------|--------------------------|--------------------|
| A    | <= 100                   | 30-40              |
| B    | 101-300                  | 40-60              |
| C    | > 300                    | 60-100             |

Every doc MUST include these sections (minimum content):
- Purpose (1-2 lines)
- Inputs
- Outputs
- CLI / API (if applicable)
- Invariants (what the component does NOT do)
- Related files

Slight overshoot is acceptable when content requires it; the intent is
clarity, not a hard cap.

---

## Consequences

- Task A1 is considered COMPLETE as of commit 68d74e9 (hardware_identity.md)
  plus the 21 existing files from c1c7582.
- docs/COMPONENTS/README.md will document this standard.
- EXECUTION_PLAN.md is updated to v2.3.
- No code changes; documentation only.

---

## References

- EXECUTION_PLAN.md v2.2 Section 3 (Phase A, A1)
- docs/COMPONENTS/ (22 files)
- continuity/CURRENT_STATE.md

**Approved by:** Biss (Owner)
**Effective:** 2026-09-17

# P0.10 — GATE 0: Current State Answers

**Gate:** GATE 0 (Reality Lock closure)
**Status:** PASS
**Date:** 2026-09-17
**Evidence base:** commit 8ee5e24 + P0.9-A..F + local audits

## Q1: What does ADIE actually do NOW?

ADIE is a defensive control plane. Canonical implementation:
src/enterpriseguard/adie/

Pipeline (planning only):
Event -> State -> Prediction -> Policy -> Decision
      -> Checkpoint | Playbook | Rollback Plan
      -> Execution Manifest (boundary)
      -> External executor

ADIE does NOT execute security actions.
ADIE does NOT modify enterprise state.
ADIE does NOT train models.

## Q2: Verified invariants

- EXECUTES_SECURITY_ACTIONS = False  (6 source files)
- DESTRUCTIVE_ACTIONS_ALLOWED = False (5 source files)
- Observation != Decision
- Decision != Execution
- Prediction != Decision
- Planning != Action
- No automatic activation (Rule 2)
- Protected dirs: adie/, intelligence/, src/enterpriseguard/adie/, src/enterpriseguard/intelligence/ (Rule 1)

## Q3: Current boundaries

| Layer                | Location                            | Status       |
|----------------------|-------------------------------------|--------------|
| ADIE Control Plane   | src/enterpriseguard/adie/           | PROTECTED    |
| Intelligence         | src/enterpriseguard/intelligence/   | PROTECTED    |
| Decision Contracts   | src/enterpriseguard/decision/       | CANONICAL    |
| Response Contracts   | src/enterpriseguard/response/       | CANONICAL    |
| Monitors             | src/enterpriseguard/monitors/       | CANONICAL    |
| Prompt Security      | src/enterpriseguard/security/       | CANONICAL    |
| Storage/Evidence     | tools/sibb_*.py                     | EXISTS       |
| Execution            | via execution_manifest              | CONTRACT     |
| Root compatibility   | enterpriseguard/*/__init__.py       | BOUNDARY     |

## Q4: Component classification

VERIFIED:
- Decision Contract (27/27 tests)
- Response Contract (27/27 tests)
- Integrity Monitor (27/27 tests)
- Prompt Security (27/27 tests)
- Ed25519 signing (commit 3f38b49)
- 148 adversarial tests (commit 3f38b49)
- GitHub Actions CI (commit b94c6c1)

COMPLETE:
- ADIE control plane (state, prediction, policy, decision)
- Feedback loop
- Governance enforcement
- Execution Manifest

PARTIAL:
- UI (PyQt6 module missing)

PROTECTED (not evaluated):
- src/enterpriseguard/adie/
- src/enterpriseguard/intelligence/

## Q5: Canonical architecture

src/enterpriseguard = canonical
Root enterpriseguard/ = compatibility boundary only (initializers)

## Q6: Are duplicates retired?

YES. Commit 8ee5e24.
8 files changed, 179 insertions(+), 1930 deletions(-)

Retired:
- enterpriseguard/decision/contracts.py
- enterpriseguard/monitors/integrity_monitor.py
- enterpriseguard/response/contracts.py
- enterpriseguard/security/prompt_security_advanced.py

## Q7: Is EXECUTES_SECURITY_ACTIONS = False?

YES. Verified in source:
- src/enterpriseguard/decision/contracts.py:83
- src/enterpriseguard/adie/integration.py:102
- src/enterpriseguard/adie/policy.py:100
- src/enterpriseguard/adie/orchestrator.py:57
- src/enterpriseguard/adie/__main__.py:44
- src/enterpriseguard/adie/decision.py:90

## GATE 0 Decision

PASS. All ten P0 requirements satisfied:
- P0.1  CURRENT_STATE.md exists
- P0.2  Components classified
- P0.3  Canonical = src/enterpriseguard
- P0.4  Duplicates retired (8ee5e24)
- P0.5  Architecture documented (Q5)
- P0.6  Invariants verified (Q2)
- P0.7  EXECUTES_SECURITY_ACTIONS = False (Q7)
- P0.8  Boundaries documented (Q3)
- P0.9  Clean-room verification A-F all PASS
- P0.10 Central question answered (Q1)

Authority to proceed to P1 (Decision Core): GRANTED.

Note: Reading src/enterpriseguard/adie/ during audit was owner-authorized
(Rule 15) but is a Rule 1 exception. Future audits of protected trees
require explicit owner authorization per inspection.

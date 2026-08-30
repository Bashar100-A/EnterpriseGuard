# EnterpriseGuard Engineering Contracts

## Preamble
This document defines the non-negotiable architectural and operational contracts for the EnterpriseGuard project. These rules govern all future development, automation, tooling, and system integrations. They are intended to protect the integrity of the project, reduce drift, and ensure operational safety across every workflow.

This contract is binding for all contributors, automated workflows, tooling, and developer agents operating within the repository. Any deviation requires explicit master authorization and written approval before action is taken.

---

## Contract I: Absolute Protection of Core Logic

### Rule
The internal core logic of EnterpriseGuard, especially the protected implementation domains, must remain immutable unless explicit master authorization has been granted in writing.

### Protected areas
The following directories are designated protected core domains and must not be modified, replaced, or bypassed under normal operation:
- `adie/`
- `intelligence/`

### Prohibition
No contributor, agent, or automated process may:
- edit files inside protected directories without explicit master authorization;
- remove, rename, or replace logic in core components;
- alter protected execution paths or policy enforcement logic;
- circumvent protections by writing compatibility patches that mutate protected runtime behavior.

### Enforcement
- Protected directories are treated as architectural boundaries.
- Any attempt to access or modify these areas without approval is a severe engineering violation.
- Changes must be implemented in the governed tooling layer or isolated extension surfaces only.

### Authority
If a change to protected logic is required, it must be submitted through a verified change approval process and explicitly granted by the governing architectural authority before implementation.

---

## Contract II: Deterministic Logging & Auditing

### Rule
All state-changing events, runs, commands, exceptions, and governance actions must be recorded in the approved operational audit locations.

### Required logs
The following files are the sanctioned audit surfaces:
- `tools/activity_log.json`
- `tools/errors.log`

### Mandatory logging behavior
Every state-changing action must be logged, including:
- application startup;
- major command execution;
- report generation;
- governance actions;
- emergency stop activation;
- any exception, runtime failure, or blocked interaction.

### Operational requirement
No silent failure is permitted. If an operation changes system state or encounters an exception, a record must be written to the appropriate audit location.

### Enforcement
- Activity events must be preserved in `tools/activity_log.json` with timestamps.
- Critical runtime or internal errors must be stored in `tools/errors.log`.
- Logs must be treated as evidence for project health, execution provenance, and operational accountability.

---

## Contract III: Zero-Doubt & Protocol Enforcement

### Rule
No ambiguous, speculative, or unverified code changes may be introduced into the project workflow.

### Minimum evidentiary standard
Before allowing advanced operations, the system must confirm:
- required governance artifacts exist;
- required runtime preconditions are satisfied;
- files and tools essential for enforcement are present;
- all checks pass through the discipline-validation process.

### Mandatory pre-flight gates
The following conditions are required before advanced workflow actions may proceed:
- required tooling metadata exists;
- activity log and governance artifacts are present;
- error-tracking infrastructure is available;
- runtime support is verified.

### Prohibited conduct
The project must not allow:
- unaudited automated edits;
- speculative changes without validation;
- actions that bypass the discipline checklist;
- unlogged or undocumented state changes.

### Enforcement
The discipline and governance layer is the standard gatekeeper. All advanced actions must pass the required checks before execution is permitted.

---

## Contract IV: Emergency Circuit Breaker

### Rule
The system must support immediate lockdown in the event of critical failure, unsafe behavior, or imposed operational emergency.

### Required mechanism
The command center must provide a clear emergency-stop control with the label:
- `EMERGENCY STOP / CIRCUIT BREAKER`

### Required behavior
When the emergency stop is triggered, the system must:
- write an emergency event to `tools/activity_log.json`;
- log the critical event to `tools/errors.log`;
- suspend further runtime actions in the current interface session;
- display a clear safe-lockdown banner to the operator;
- prevent normal operational flows until manual reset and review are performed.

### Enforcement
Emergency-stop behavior is considered a core safety invariant. It is mandatory for governance and operational continuity.

---

## Architectural Invariants

The following invariants are permanent:
1. Protected core logic remains safe from unauthorized edits.
2. All significant actions are auditable and timestamped.
3. No workflow proceeds without discipline validation.
4. Emergency lockdown exists as a final safety layer.
5. Tooling and governance logic must remain outside protected implementation domains.
6. The repository architecture must prioritize safety, clarity, and traceability over convenience.

---

## Compliance Statement
Any contributor, tool, or automation operating in this repository agrees to uphold these contracts. Failure to comply constitutes a direct violation of project governance and may require corrective action, rollback, or formal review.

This document is intended to be a permanent governing standard for the EnterpriseGuard project.

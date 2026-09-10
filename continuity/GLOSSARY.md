# EnterpriseGuard ADIE — Glossary

This file unifies the terminology used across the project.

**Governed by:** continuity/RULES.md  
**Updated:** 2026-09-02

---

## A

### ADIE
Adaptive Defense Intelligence Engine. The decision core of EnterpriseGuard.

### Audit Chain
The tamper-evident hash chain that protects `activity_log.json`.

### Atomic Write
A write pattern using `tempfile.mkstemp` and `os.replace` to prevent
partial or corrupted files.

---

## C

### Central Test Results Log
`tests/TEST_RESULTS.md`. The permanent record of unit test executions.

### Continuity Folder
`continuity/`. The collection of permanent reference files that allow
full memory recovery after a conversation ends.

### Critical Files
Files that must never be deleted: baselines, sentinels,
`hardware_identity.json`, and `genesis_baseline.json`.

---

## D

### Decision Plane
The layer where ADIE analyzes, decides, and plans. It never executes.

### Distributed Proof
The fourth proof component. It splits a proof digest into three
shards: local, external, and physical.

### Dynamic Files
Files excluded from integrity monitoring because they change
frequently: `activity_log.json`, `errors.log`, `TEST_RESULTS.md`,
`continuity/CURRENT_STATE.md`.

---

## E

### Ephemeral Feeding Cell
The philosophy that ADIE should feed on attacks, doubt itself, forget
without denial, and regenerate proof continuously.

### Execution Plane
The external layer that executes actions after ADIE approval.

---

## G

### Genesis Seed
The second proof component. It proves the system did not originate
from nothing.

---

## H

### Hardware Identity
The first proof component. It binds ADIE to specific hardware
fingerprints to prevent cloning.

### Hash-Based Logical Clock
A time-independent ordering mechanism based on SHA-256 hashes instead
of system time.

---

## I

### Innocence Chain
The fifth proof component. It creates a continuous chain of proof
rings that regenerate integrity evidence.

### Integrity Monitor
The tool that validates file baselines against sentinels.

---

## P

### Participatory Proof
Another name for Distributed Proof; no single witness can prove the
system alone.

### Protected Directories
`adie/`, `intelligence/`, and their `src/enterpriseguard/` equivalents.
They are never read or modified.

---

## R

### Relational Memory
The third proof component. It stores causal links between events,
allowing forgetting without denial.

### Renewed Innocence
The principle behind Innocence Chain: continuously proving the system
has not been silently modified.

---

## S

### Sovereign Reference Core
The highest architectural concept. ADIE is a self-verifying,
self-evolving proof core, not a traditional security tool.

### Sentinel
A file that stores the SHA-256 of a protected baseline file to detect
tampering.

---

## T

### Tissue Identity
Another name for Hardware Identity.

---

## W

### Workflow Discipline
The enforced practice of one responsibility per command, raw evidence,
manual sensitive documents, and immediate stop on critical errors.
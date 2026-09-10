# EnterpriseGuard ADIE — Ideas Backlog

This file records deferred and future ideas that must not be forgotten.

**Governed by:** continuity/RULES.md  
**Updated:** 2026-09-02

---

## Deferred Ideas

### 1. Toxic Mirror (DC-028)
- **Status:** Deferred until isolated environment.
- **Description:** A deceptive interface that traps attackers.
- **Reason:** Legal and security risk; requires Docker/Podman isolation.

### 2. Self-Evolving Defense Core
- **Status:** Deferred.
- **Description:** Closed-loop attack generation and patching with
  distributed authority.
- **Condition:** Deploy only after 100 successful cycles.

### 3. Hardware Identity Regeneration UI
- **Status:** Future.
- **Description:** Owner-friendly flow to regenerate identity key with
  clear audit logging.

### 4. External Proof Shard via Private Git
- **Status:** Future.
- **Description:** Automatically push the external shard to a private
  Git repository instead of a local fallback.

### 5. Periodic Innocence Ring Automatic Generation
- **Status:** Future.
- **Description:** Systemd timer that generates a new ring at a
  configurable interval, installed disabled by default.

### 6. Centralized Backup Rotation
- **Status:** Future.
- **Description:** Automatic compression and rotation of old backups
  while preserving audit history.

### 7. Type Annotations Cleanup (Pylance)
- **Status:** Deferred.
- **Description:** Add complete type annotations to reduce static
  analysis warnings.

### 8. Enterprise Web Interface
- **Status:** Future.
- **Description:** Replace Streamlit with FastAPI + React for
  enterprise deployment.

### 9. SIEM Integration
- **Status:** Future.
- **Description:** Native connectors for SIEM platforms and
  OpenTelemetry.

---

## Rules for This File

- Never delete an idea. Mark it as superseded or completed.
- Deferred ideas remain here until explicitly implemented.
- New ideas are appended at the end with status `Future`.
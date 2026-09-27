# Changelog

All notable changes to EnterpriseGuard → ADIE are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-01

### Added
- Architectural Vision document (`docs/ARCHITECTURAL_VISION.md`) defining the Sovereign Reference Core.
- Commercial Roadmap document (`business/COMMERCIAL_ROADMAP.md`) with scarcity strategy.
- Governance decisions `DC-042` and `DC-043` recorded.

### Changed
- Project Memory updated to reflect current actual state and next actions.

### Fixed
- DC identifier numbering gap resolved (DC-042 and DC-043 now sequential after DC-041).

### Security
- Protected directories (`adie/`, `intelligence/`) remain unopened and untouched.

## [0.1.0] - 2026-09-01

### Added
- Core decision engine and security control plane architecture.
- Governance tools: `checklist.py`, `integrity_monitor.py`, `audit_chain.py`.
- Utility modules: `time_utils.py`, `audit_chain.py`.
- Ephemeral feeding cell components: `ephemeral_archiver.py`, `logical_clock.py`, `attack_analyzer.py`.
- Compliance Matrix document (`docs/DC-038_COMPLIANCE_MATRIX.md`).
- Patent ideas documents (`docs/PATENT_IDEAS.md`, `docs/PATENT_IDEAS_AR.md`).
- Deployment files: `deploy/enterpriseguard.conf`, `deploy/enterpriseguard.service`, `deploy/enterpriseguard-timer.service`.
- Installer and uninstaller scripts (`tools/installer.py`, `tools/uninstall.py`).
- Release signing tool (`tools/sign_release.py`).

### Fixed
- Self-inflicted integrity drift by excluding dynamic append-only files from monitoring.
- Duplicate DC identifier conflicts.

### Security
- Protected directories (`adie/`, `intelligence/`) remain unopened and untouched.

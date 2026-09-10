
> New: open_verifier.py (MIT), rfc3161 dynamic TSA, dashboard.
> New in prototype: `tools/aaac_connector.py` (Langfuse integration), `tools/ring_storage.jsonl` (agent events), `tools/send_test_trace.py` (test trace sender).
> Strategic direction: Self-imposing compliance layer.
> Current phase: Customer Discovery (No Development)
> Strategic direction: AAAC is a proof layer added on top of existing monitoring tools, not a replacement.
> Development freeze: active until 2026-09-20.

# EnterpriseGuard ADIE — Components Inventory

This file is a quick reference of all existing project components,
their current status, and progress.

**Governed by:** continuity/RULES.md  
**Updated:** 2026-09-02

| Component | File | Progress | Status |
|-----------|------|----------|--------|
| Hardware Identity | tools/hardware_identity.py | 100% | ✅ Complete |
| Genesis Seed | tools/genesis_seed.py | 100% | ✅ Complete |
| Relational Memory | tools/relational_memory.py | 100% | ✅ Complete |
| Distributed Proof | tools/distributed_proof.py | 100% | ✅ Complete |
| Governance Checklist | tools/checklist.py | 100% | ✅ Complete |
| Integrity Monitor | tools/integrity_monitor.py | 100% | ✅ Complete |
| Audit Chain | tools/audit_chain.py | 100% | ✅ Complete |
| Ephemeral Archiver | tools/ephemeral_archiver.py | 100% | ✅ Complete |
| Logical Clock | tools/logical_clock.py | 100% | ✅ Complete |
| Attack Analyzer | tools/attack_analyzer.py | 100% | ✅ Complete |
| Installer | tools/installer.py | 90% | ✅ Mostly Complete |
| Uninstaller | tools/uninstall.py | 100% | ✅ Complete |
| Release Signing | tools/sign_release.py | 100% | ✅ Complete |
| Time Utils | tools/time_utils.py | 100% | ✅ Complete |
| Time Drift Detector | tools/time_drift.py | 100% | ✅ Complete |
| Hybrid Retrieval | tools/hybrid_retrieval.py | 100% | ✅ Complete |
| RAG System | tools/rag_system.py | 100% | ✅ Complete |
| Governance Rule Generator | tools/governance_rule_generator.py | 100% | ✅ Complete |
| Command Center | tools/command_center.py | 100% | ✅ Complete |
| Discipline | tools/discipline.py | 100% | ✅ Complete |
| Integration Test | tools/integration_test.py | 100% | ✅ Complete |
| Real-Time Monitor | tools/realtime_monitor.py | 100% | ✅ Complete |
| Innocence Chain | tools/innocence_chain.py | 100% | ✅ Complete (with digital signatures) |
| Static Analysis | tools/bandit_report.json, tools/pip_audit_report.json | 100% | ✅ Complete (Medium=0) |
| Time Spoofing Resistance | tools/time_spoof_test.sh | 100% | ✅ Complete |
| Real-Time Monitor | tools/realtime_monitor.py | 100% | ✅ Complete |
| Advanced Security Tests | tests/ADVANCED_SECURITY_TESTS.md | 100% | ✅ Complete |
| Load Resilience | tools/ddos_test.sh | 100% | ✅ Complete |
| Time Spoofing Resistance | tools/time_spoof_test.sh | 100% | ✅ Complete |
| Resource Starvation Resistance | tools/resource_starvation_test.sh | 100% | ✅ Complete |
| Collision Resistance | tools/collision_test.sh | 100% | ✅ Complete |
| Technical Whitepaper | docs/WHITEPAPER.md | 100% | ✅ Complete |
| Dimensional State | tools/dimensional_state.py | 100% | ✅ Complete |
| Dimensional Collector | tools/dimensional_collector.py | 100% | ✅ Complete |
| Dimensional Decision Engine | tools/dimensional_decision_engine.py | 100% | ✅ Complete |
| Dimensional Decision Engine Calibrated | tools/dimensional_decision_engine_calibrated.py | 100% | ✅ Complete |
| Dimensional State | tools/dimensional_state.py | 100% | ✅ Complete |
| Dimensional Collector | tools/dimensional_collector.py | 100% | ✅ Complete |
| Dimensional Decision Engine | tools/dimensional_decision_engine.py | 100% | ✅ Complete (calibrated, official) |
| Relational Memory JSON | tools/relational_memory.json | 100% | ✅ Complete (empty schema) |
| Genesis Signature | tools/genesis_public_key.pem, ~/.enterpriseguard/keys/genesis_private_key.pem | 100% | ✅ Complete |
| Sovereign Installer | install.sh | 100% | ✅ Complete |
| Centralized Paths Config | tools/paths_config.py | 100% | ✅ Complete |
| Anomaly Detector (Draft) | backups/anomaly_detector_draft_*.py | 0% | ⏸️ Deferred |
| SIBB CLI | tools/sibb_cli.py | 100% | ✅ Complete (v1.1, 17/17 tests) |
| SIBB-Innocence Integration | tools/sibb_innocence_integration.py | 100% | ✅ Complete (v1.3, 15/15 tests) |
- DC-068: Genesis Signature implemented in innocence_chain.py
- DC-069: Sovereign Installer tested
- DC-070: Anomaly Detector deferred
- DC-071: Dynamic paths migrated to paths_config.py
| Dimensional History Recorder | tools/dimensional_history_recorder.py | 100% | ✅ Complete |
| Dimensional History Data | tools/dimensional_history.jsonl | 100% | ✅ Complete (100 samples) |

| SIBB (Immutable Storage) | tools/sibb_*.py | 100% | ✅ Complete |
| SIBB Storage | tools/sibb_storage.py | 100% | ✅ Complete (v7.2, 19/19 tests) |
| SIBB Distributed Storage | tools/sibb_distributed.py | 100% | ✅ Complete (v1.2, 23/23 tests) |
| SIBB Key Management | tools/sibb_keys.py | 100% | ✅ Complete (v1.0.3, 29/29 tests) |

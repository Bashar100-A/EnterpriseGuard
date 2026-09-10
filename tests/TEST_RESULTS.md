# EnterpriseGuard ADIE — Central Test Results Log

This file is the permanent, append-only record of all unit test executions.

**Governed by:** DC-047  
**Policy:** This file is dynamic and is excluded from integrity monitoring and trusted baselines. It may be updated manually by the owner after every test run.

**Rule:** Every test run is recorded. The latest result for each component is the authoritative one. Old rows are never deleted.

| Date | Component | Test File | Result | Tests | Exit Code | Linked DC | Notes |
|------|-----------|-----------|--------|-------|-----------|-----------|-------|
| 2026-09-01 | hardware_identity | tests/test_hardware_identity.py | PASS | 6 | 0 | DC-044 | None |
| 2026-09-02 | genesis_seed | tests/test_genesis_seed.py | PASS | 7 | 0 | DC-045 | None |
| 2026-09-02 | relational_memory | tests/test_relational_memory.py | PASS | 5 | 0 | DC-046 | None |
| 2026-09-02 | distributed_proof | tests/test_distributed_proof.py | PASS | 9 | 0 | DC-049 | None |
| 2026-09-02 | innocence_chain | tests/test_innocence_chain.py | PASS | 13 | 0 | DC-051 | None |
| 2026-09-02 | Internal Security ST-001 | /tmp/enterpriseguard_test/st001_permission_test.sh | PASS | 1 | 0 | DC-052 | Permission check: 600 |
| 2026-09-02 | Internal Security ST-002 | /tmp/enterpriseguard_test/st002_protected_dirs_test.sh | PASS | 4 | 0 | DC-052 | Protected dirs absent |
| 2026-09-02 | Internal Security ST-003 | /tmp/enterpriseguard_test/st003_relational_memory_test.py | PASS | 3 | 0 | DC-052 | Input validation |
| 2026-09-02 | Internal Security ST-004 | /tmp/enterpriseguard_test/st004_innocence_chain_tamper_test.py | PASS | 2 | 0 | DC-052 | Tamper detection |
| 2026-09-02 | Internal Security ST-005 | /tmpTEST_RTEST_RESULTSESULTS/enterpriseguard_test/st005_distributed_proof_missing_shard_test.sh | PASS | 1 | 0 | DC-052 | Missing shard rejection |
| 2026-09-02 | innocence_chain | tests/test_innocence_chain.py | PASS | 13 | 0 | DC-055 | Digital signature added; tests still pass |
| 2026-09-03 | Dimensional Engine Calibration | tools/dimensional_collector.py + dimensional_decision_engine_calibrated.py | PASS | 7 | 0 | DC-066 | Calibration tests passed; decision CONTINUE |
| 2026-09-03 | Sovereign Stabilization | tools/dimensional_collector.py + tools/dimensional_decision_engine.py | PASS | 7 | 0 | DC-067 | Calibrated engine official; decision CONTINUE with critical dimensions healthy |
| 2026-09-04 | Genesis Signature | tools/innocence_chain.py | PASS | 1 | 0 | DC-068 | VERIFIED_OK with chain_id and genesis_signature |
| 2026-09-04 | Sovereign Installer | install.sh + enterpriseguard CLI | PASS | 3 | 0 | DC-069 | Install/check/verify-chain/uninstall in /tmp/test_install; FAILURE:0 |
| 2026-09-04 | Centralized Paths Migration | tools/paths_config.py | PASS | 6 | 0 | DC-071 | All main tools now use centralized dynamic paths |
| 2026-09-04 | M2 Sovereign Installer & Paths Migration | install.sh + paths_config.py | PASS | 6 | 0 | DC-071 | M2 complete; M3 deferred; M4 pending |
| 2026-09-04 | Dimensional History Recorder | tools/dimensional_history_recorder.py | PASS | 1 | 0 | DC-072 | Records state to dimensional_history.jsonl, logs activity |
| 2026-09-04 | Dimensional History Collection | /tmp/collect_history.sh | PASS | 100 | 0 | DC-073 | Collected 100 real samples; all spatial scores 1.0 |
| 2026-09-08T11:54:43Z | SIBB Storage | tests/test_sibb_storage.py | PASS | 19 | 0 | DC-122 | All unit/security tests passed after v7.2 fixes. |
| 2026-09-08T13:03:30Z | SIBB Distributed Storage | tests/test_sibb_distributed.py | PASS | 23 | 0 | DC-123 | All unit/security tests passed after v1.2. |
| 2026-09-08T13:40:57Z | SIBB Key Management | tests/test_sibb_keys.py | PASS | 29 | 0 | DC-124 | All unit/security tests passed after v1.0.3. |
| 2026-09-08T14:18:15Z | SIBB CLI | tests/test_sibb_cli.py | PASS | 17 | 0 | DC-125 | All unit/security tests passed after v1.1. |
| 2026-09-08T15:44:00Z | SIBB-Innocence Integration | tests/test_sibb_innocence_integration.py | PASS | 15 | 0 | DC-126 | All unit/security tests passed after v1.3. |

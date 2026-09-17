# Components Documentation

This directory documents the 20+ core components of EnterpriseGuard ADIE.

## Standard (DC-135)

Doc length is tiered by component code size:

| Tier | Code size (Python lines) | Doc target |
|------|--------------------------|------------|
| A    | <= 100                   | 30-40 lines |
| B    | 101-300                  | 40-60 lines |
| C    | > 300                    | 60-100 lines |

Every doc MUST include:
- Purpose
- Inputs
- Outputs
- CLI / API (if applicable)
- Invariants (what the component does NOT do)
- Related files

## Index

Sovereign Reference Core (5):
- hardware_identity.md
- genesis_seed.md
- relational_memory.md
- distributed_proof.md
- innocence_chain.md

Integrity and Audit (4):
- audit_chain.md
- integrity_monitor.md
- realtime_monitor.md
- time_utils.md

SIBB Storage Layer (5):
- sibb_storage.md, sibb_storage_part2.md, sibb_storage_part3.md
- sibb_keys.md
- sibb_distributed.md
- sibb_cli.md
- sibb_innocence_integration.md

Signing and Compliance (3):
- signing_backend.md
- compliance_engine.md
- paths_config.md

HTTP and Integration (2):
- sovereign_http_server.md
- aaac_connector.md

Optional / PoC (1):
- blockchain_anchor.md

## Rule

New docs MUST follow the tiered standard. Existing docs are grandfathered
until a future revision task.

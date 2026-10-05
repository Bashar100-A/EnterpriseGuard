# ADIE-REGISTRY v0.1 — Registry and Compatibility

**Status:** Normative
**Branch:** vOmega
**Date:** 2026-10-06
**Depends on:** META-CONTRACT-0.1, ERROR-REGISTRY-0.1
**Satisfies:** I17, I19, M05, M17, M26, M28, M29, M39

## §0. Standing

Defines the Registry subsystem: how templates, rewrite rules, and
compatibility relations are represented as first-class MetaObjects and
how they are looked up deterministically.

Registry is an artifact store, not a decision engine.
It answers "what is declared" — never "what is compatible".

## §1. Scope

The Registry holds three kinds of entries:

- template       (referenced by authoring compiler)
- rewrite_rule   (referenced by proof-carrying semantic equivalence)
- compatibility  (relation between two versioned objects)

Every entry is a MetaObject per META-CONTRACT §2:

    O = (type, id, version, payload, status, prev, effective, expiry,
         issuer, digest)

## §2. Namespace rule

Every entry's `id` MUST be `<namespace>:<local_id>`.

- namespace matches `^[a-z][a-z0-9_]{0,31}$`
- local_id matches `^[A-Za-z0-9_.\-]{1,128}$`
- namespace MUST be declared in the Manifest Universe (I19)
- A cross-namespace collision (same id in two namespaces) is permitted
  only if the namespaces are independently registered. Lookup is always
  namespace-qualified.

## §3. Registry entry schema

    {
      "type": "template" | "rewrite_rule",
      "id": "<namespace>:<local_id>",
      "version": "<semver-ish string>",
      "payload": { ... },
      "status": "ACTIVE" | "DEPRECATED" | "REVOKED",
      "effective": "<RFC3339 UTC Z>" | null,
      "expiry": "<RFC3339 UTC Z>" | null,
      "issuer": "<key_id>",
      "digest": "sha256:..."
    }

digest = H_A("registry-entry", canonical_bytes(O_without_digest))

## §4. Compatibility record schema

    {
      "type": "compatibility",
      "from": "<id>",
      "to": "<id>",
      "relation": "EXACT" | "ENCODING" | "SEMANTIC" | "INCOMPATIBLE",
      "scope": [<string>, ...],
      "constraints": { ... },
      "proof_digest": "sha256:..." | null,
      "authority": "<key_id>",
      "effective": "<RFC3339 UTC Z>",
      "expiry": "<RFC3339 UTC Z>" | null,
      "issuer": "<key_id>",
      "digest": "sha256:..."
    }

## §5. Lookup rules

- Lookup is always exact: (from, to) → record or None.
- No transitive inference (I17). If a→b and b→c exist, a→c still None.
- No version-tuple inference. "1.0" and "1.0.0" are distinct strings.
- Lookup may filter by status; a DEPRECATED record is returned but flagged.

## §6. Status lifecycle

Template/Rewrite entry states:

    PROPOSED -> ACTIVE -> DEPRECATED -> REVOKED

Transitions:
- PROPOSED -> ACTIVE: allowed (register)
- ACTIVE -> DEPRECATED: allowed (deprecate)
- DEPRECATED -> REVOKED: allowed (revoke)
- ACTIVE -> REVOKED: allowed (revoke directly)
- Any -> PROPOSED: forbidden
- REVOKED -> *: forbidden

Compatibility record states:

    ACTIVE -> DEPRECATED -> REVOKED

Same rules.

## §7. Effective and expiry

- If `effective` is null, entry is active from registration.
- If `expiry` is null, entry never expires.
- Lookup with `now` parameter:
  - entry.effective > now  -> NOT_YET_EFFECTIVE
  - entry.expiry <= now    -> EXPIRED
- Both produce `E-META-25` (entry) or `E-META-26` (compatibility).

## §8. Scope (compatibility only)

`scope` is a list of capability strings. A verifier requesting a
capability MUST find it in `scope`. Absent capability -> `E-META-27`.

Empty scope list -> valid (means "all contexts").

## §9. Fork detection

Given two snapshots of the Registry (e.g., from two manifests), if:

    id in snapshot_a AND id in snapshot_b
    AND snapshot_a[id].digest != snapshot_b[id].digest

then this is a Registry Fork. The resolver MUST NOT choose.
It raises `E-META-13` (Registry Fork) — same code as intra-snapshot fork.

## §10. Snapshot replay detection

A snapshot carries a `snapshot_epoch`. If a caller provides a `known_epoch`
greater than the snapshot's epoch, the snapshot is stale and MUST be
rejected with `E-META-28`.

## §11. Failure codes

From ERROR-REGISTRY-0.1:

- E-META-13   Registry fork (intra- or inter-snapshot)
- E-META-16a  Malformed entry schema
- E-META-16c  Invalid lifecycle transition
- E-META-17   Compatibility inference attempted / missing proof
- E-META-19   Namespace not in Universe
- E-META-23   Malformed id (namespace:local_id rule)
- E-META-24   Invalid status value
- E-META-25   Entry not yet effective or expired
- E-META-26   Compatibility expired
- E-META-27   Compatibility scope mismatch
- E-META-28   Registry snapshot replay

## §12. Non-goals

- No priority resolution between conflicting compat records
- No policy interpretation
- No network or filesystem lookups
- No version normalization ("1.0" != "1.0.0")
- No caching; determinism is required even with repeated lookups

## §13. Invariants (explicit)

- I17: no compatibility inference
- I19: every namespace declared in Universe
- I14/I15: version strings are distinct identities
- I13: lookups deterministic

## §14. Amendment

New versions (0.2, 0.3). Append-only.

End of ADIE-REGISTRY-0.1

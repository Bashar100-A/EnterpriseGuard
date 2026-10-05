"""ADIE vΩ — Meta-layer core (Phase 1.6, satisfies META-CONTRACT-0.1)."""
from protocol.core.domain_hash import H_A
from protocol.core.jcs import canonical_bytes


class MetaError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")


ALLOWED_EVENTS = frozenset({
    "REGISTER_TEMPLATE", "REGISTER_REWRITE_RULE",
    "DECLARE_COMPATIBILITY", "DEPRECATE_VERSION",
    "REVOKE_KEY", "ROTATE_ROOT",
    "FREEZE_REGISTRY", "RESUME_REGISTRY",
    "DECLARE_MIGRATION",
})

ALLOWED_RELATIONS = frozenset({"EXACT", "ENCODING", "SEMANTIC", "INCOMPATIBLE"})

KEY_ROLES = frozenset({"ROOT", "MANIFEST", "ISSUER", "EPHEMERAL"})

KEY_STATES = frozenset({
    "PROVISIONED", "ACTIVE", "SUSPENDED", "REVOKED",
    "COMPROMISED", "EXPIRED", "RETIRED",
})

COMPILER_DIGEST = "sha256:" + "c" * 64


class MetaObject:
    ALLOWED_TYPES = frozenset({
        "template", "rewrite_rule", "compatibility", "manifest",
        "key_lifecycle", "policy",
    })

    def __init__(self, type, id, version, payload, status="ACTIVE", issuer=None):
        if type not in self.ALLOWED_TYPES:
            raise MetaError("E-META-16a", f"unknown type {type!r}")
        self.type = type
        self.id = id
        self.version = version
        self.payload = payload
        self.status = status
        self.issuer = issuer
        self.digest = self._digest()

    def _digest(self):
        body = {
            "type": self.type, "id": self.id, "version": self.version,
            "payload": self.payload, "status": self.status,
            "issuer": self.issuer,
        }
        return "sha256:" + H_A("meta-object", canonical_bytes(body)).hex()

    def to_dict(self):
        return {
            "type": self.type, "id": self.id, "version": self.version,
            "payload": self.payload, "status": self.status,
            "issuer": self.issuer, "digest": self.digest,
        }


class Universe:
    def __init__(self, acl_versions, template_ids, rewrite_ids,
                 registry_namespaces, algorithms, compat_relations):
        self.acl_versions = frozenset(acl_versions)
        self.template_ids = frozenset(template_ids)
        self.rewrite_ids = frozenset(rewrite_ids)
        self.registry_namespaces = frozenset(registry_namespaces)
        self.algorithms = frozenset(algorithms)
        self.compat_relations = frozenset(compat_relations)

    def contains_template(self, tid):
        if tid not in self.template_ids:
            raise MetaError("E-META-19", f"template {tid!r} not in universe")
        return True

    def contains_rewrite(self, rid):
        if rid not in self.rewrite_ids:
            raise MetaError("E-META-19", f"rewrite {rid!r} not in universe")
        return True

    def size(self):
        return (len(self.acl_versions) + len(self.template_ids)
                + len(self.rewrite_ids) + len(self.registry_namespaces)
                + len(self.algorithms) + len(self.compat_relations))


class Manifest:
    def __init__(self, epoch, prev_epoch, universe, threshold_k, threshold_n,
                 signatures, digest=None):
        if threshold_k < 1 or threshold_n < threshold_k:
            raise MetaError("E-META-16b", "invalid threshold")
        self.epoch = epoch
        self.prev_epoch = prev_epoch
        self.universe = universe
        self.threshold_k = threshold_k
        self.threshold_n = threshold_n
        self.signatures = list(signatures)
        self.digest = digest or self._digest()

    def _digest(self):
        body = {
            "epoch": self.epoch, "prev_epoch": self.prev_epoch,
            "threshold": [self.threshold_k, self.threshold_n],
            "universe_size": self.universe.size(),
        }
        return "sha256:" + H_A("manifest", canonical_bytes(body)).hex()

    def verify_threshold(self):
        uniq = set(self.signatures)
        if len(uniq) < self.threshold_k:
            raise MetaError("E-META-16d",
                f"threshold {self.threshold_k}/{self.threshold_n} not met "
                f"(got {len(uniq)} unique)")


class Registry:
    def __init__(self):
        self.templates = {}
        self.rewrites = {}
        self.compat = {}

    def register_template(self, tid, digest):
        if tid in self.templates:
            if self.templates[tid] != digest:
                raise MetaError("E-META-13",
                    f"template {tid!r} already registered with different digest")
            return
        self.templates[tid] = digest

    def register_rewrite(self, rid, digest):
        if rid in self.rewrites:
            if self.rewrites[rid] != digest:
                raise MetaError("E-META-14",
                    f"rewrite {rid!r} shadowed")
            return
        self.rewrites[rid] = digest

    def declare_compat(self, from_id, to_id, relation, proof_digest=None):
        if relation not in ALLOWED_RELATIONS:
            raise MetaError("E-META-17", f"unknown relation {relation!r}")
        if relation == "SEMANTIC" and not proof_digest:
            raise MetaError("E-META-17",
                "SEMANTIC compatibility requires proofDigest")
        self.compat[(from_id, to_id)] = {
            "relation": relation, "proof_digest": proof_digest,
        }

    def lookup_compat(self, from_id, to_id):
        # NO INFERENCE. Only exact declared relations.
        return self.compat.get((from_id, to_id))


class KeyState:
    def __init__(self, key_id, role, state="PROVISIONED"):
        if role not in KEY_ROLES:
            raise MetaError("E-META-16d", f"unknown role {role!r}")
        if state not in KEY_STATES:
            raise MetaError("E-META-16c", f"unknown state {state!r}")
        self.key_id = key_id
        self.role = role
        self.state = state

    def can_sign(self, object_type):
        if self.state != "ACTIVE":
            raise MetaError("E-META-16d", f"key {self.key_id} not ACTIVE")
        if object_type == "daily_claim" and self.role != "ISSUER":
            raise MetaError("E-META-16d",
                f"role {self.role} cannot sign daily_claim")
        if object_type == "manifest" and self.role != "MANIFEST":
            raise MetaError("E-META-16d",
                f"role {self.role} cannot sign manifest")


class StateMachine:
    """F_M: (M, event) -> M'.  Deterministic, total on ALLOWED_EVENTS."""

    def __init__(self):
        self.epoch = 0
        self.frozen = False
        self.registry = Registry()
        self.keys = {}
        self.applied_events = set()

    def apply(self, event):
        etype = event.get("type")
        if etype not in ALLOWED_EVENTS:
            raise MetaError("E-META-13", f"unknown event {etype!r}")

        if self.frozen and etype != "RESUME_REGISTRY":
            raise MetaError("E-META-13", "registry is frozen")

        prev = event.get("prev_epoch")
        new = event.get("new_epoch")
        if prev != self.epoch:
            raise MetaError("E-META-13",
                f"prev_epoch {prev} != current {self.epoch}")
        if new != self.epoch + 1:
            raise MetaError("E-META-13",
                f"epoch must increment by 1 (got {prev} -> {new})")

        eid = event.get("event_id")
        if eid in self.applied_events:
            raise MetaError("E-META-13", f"event {eid} replayed")

        if etype == "REGISTER_TEMPLATE":
            self.registry.register_template(event["id"], event["digest"])
        elif etype == "REGISTER_REWRITE_RULE":
            self.registry.register_rewrite(event["id"], event["digest"])
        elif etype == "DECLARE_COMPATIBILITY":
            self.registry.declare_compat(
                event["from"], event["to"],
                event["relation"], event.get("proof_digest"))
        elif etype == "FREEZE_REGISTRY":
            self.frozen = True
        elif etype == "RESUME_REGISTRY":
            self.frozen = False
        elif etype == "REVOKE_KEY":
            kid = event["key_id"]
            if kid in self.keys:
                self.keys[kid].state = "REVOKED"
        elif etype == "ROTATE_ROOT":
            pass

        self.applied_events.add(eid)
        self.epoch = new


class Compiler:
    """Deterministic compiler. All inputs declared, no hidden reads."""

    @classmethod
    def compile(cls, template, params, manifest, env=None):
        declared = set(template.get("declared_params", []))
        required = set(template.get("required_params", []))

        for p in required:
            if p not in params:
                raise MetaError("E-META-18", f"missing required param {p!r}")
        for p in params:
            if p not in declared:
                raise MetaError("E-META-18", f"undeclared param {p!r}")

        if env:
            for k in template.get("forbidden_env", []):
                if k in env:
                    raise MetaError("E-META-20", f"compiler read env {k!r}")

        if manifest is None or not manifest.digest:
            raise MetaError("E-META-20", "manifest digest missing")

        closure = {
            "template_digest": template.get("digest"),
            "param_digest": "sha256:" + H_A("params",
                canonical_bytes(params)).hex(),
            "compiler_digest": COMPILER_DIGEST,
            "acl_version": template.get("acl_version"),
            "ast_digest": "sha256:" + H_A("ast",
                canonical_bytes(template.get("ast", {}))).hex(),
            "meta_manifest_digest": manifest.digest,
        }

        required_fields = {
            "template_digest", "param_digest", "compiler_digest",
            "acl_version", "ast_digest", "meta_manifest_digest",
        }
        missing = required_fields - closure.keys()
        if missing:
            raise MetaError("E-META-20", f"closure missing: {missing}")

        return closure


def verify_offline(claim_epoch, verifier_known_epoch):
    """I22: offline verifier must not PASS claims newer than known epoch."""
    if claim_epoch > verifier_known_epoch:
        raise MetaError("E-META-22",
            f"claim depends on epoch {claim_epoch}, verifier knows {verifier_known_epoch}")
    return True


FORBIDDEN_IMPORTS = frozenset({
    "socket", "urllib", "requests", "http", "httpx", "subprocess",
    "os.system", "asyncio.subprocess",
})


def check_purity(template):
    """I21: template must declare purity PURE and no forbidden imports."""
    purity = template.get("purity")
    if purity != "PURE":
        raise MetaError("E-META-21",
            f"template purity must be PURE, got {purity!r}")
    for imp in template.get("imports", []):
        for f in FORBIDDEN_IMPORTS:
            if imp == f or imp.startswith(f + "."):
                raise MetaError("E-META-21", f"forbidden import {imp!r}")
    return True

"""ADIE vΩ — Binding verification (Phase 1)."""
from .domain_hash import H_A
from .jcs import canonical_bytes


PURPOSE_DEPLOYMENT_AUTHORIZATION = 7

PURPOSE_REGISTRY = {
    7: "DEPLOYMENT_AUTHORIZATION",
}


class BindingError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")


def request_hash(request: dict) -> str:
    return "sha256:" + H_A("request", canonical_bytes(request)).hex()


def verify_binding(binding: dict, request: dict,
                   expectation: dict | None = None) -> None:
    """Raise BindingError on any mismatch."""
    required = ["audience", "purpose", "resource",
                "request_hash", "nonce", "certificate_id"]
    for f in required:
        if f not in binding:
            raise BindingError("E_BINDING_MISSING_FIELD", f)

    if not isinstance(binding["audience"], str) or not binding["audience"]:
        raise BindingError("E_BINDING_AUDIENCE", str(binding["audience"])[:40])
    if not isinstance(binding["purpose"], int) or binding["purpose"] not in PURPOSE_REGISTRY:
        raise BindingError("E_BINDING_PURPOSE", str(binding["purpose"])[:40])
    if not isinstance(binding["resource"], str) or "://" not in binding["resource"]:
        raise BindingError("E_BINDING_RESOURCE", str(binding["resource"])[:40])

    recomputed = request_hash(request)
    if recomputed != binding["request_hash"]:
        raise BindingError("E_BINDING_REQUEST_HASH",
                           f"expected {binding['request_hash'][:20]}, got {recomputed[:20]}")

    if expectation:
        for k in ("audience", "purpose", "resource"):
            if k in expectation and expectation[k] != binding[k]:
                raise BindingError(f"E_BINDING_{k.upper()}_MISMATCH",
                                   f"expected {expectation[k]}, got {binding[k]}")

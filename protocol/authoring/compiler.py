"""ADIE-AUTHORING v0.1 — Python reference compiler (Phase 1.8).

Frozen Compiler binds (code_digest, manifest, acl_version).
compile(template, params) is pure and deterministic.
Output is the Authoring Closure (AClosure), exactly six fields.
"""
from dataclasses import dataclass

from protocol.core.domain_hash import H_A
from protocol.core.jcs import canonical_bytes
from protocol.acl.ast import validate as acl_validate, ACLError
from protocol.acl.normalize import canonical_ast
from protocol.meta.core import Manifest


CODE_VERSION = "AUTHORING-0.1"
ACL_VERSION = "0.1"

_CODE_DIGEST = "sha256:" + H_A(
    "compiler-code", CODE_VERSION.encode("utf-8")).hex()

REQUIRED_CLOSURE_KEYS = frozenset({
    "template_digest",
    "parameter_digest",
    "compiler_digest",
    "acl_version",
    "canonical_ast_digest",
    "meta_manifest_digest",
})


class AuthoringError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")


@dataclass(frozen=True)
class Compiler:
    manifest: Manifest
    acl_version: str = ACL_VERSION

    def __post_init__(self):
        if not isinstance(self.manifest, Manifest):
            raise AuthoringError(
                "E-META-20",
                f"manifest must be a Manifest instance, got {type(self.manifest).__name__}")
        if not self.manifest.digest:
            raise AuthoringError("E-META-20", "manifest.digest is empty")
        if self.acl_version != ACL_VERSION:
            raise AuthoringError(
                "E-META-14",
                f"unsupported acl_version {self.acl_version!r}; expected {ACL_VERSION!r}")

    @property
    def code_digest(self) -> str:
        return _CODE_DIGEST

    @property
    def identity(self) -> str:
        body = {
            "code_digest": self.code_digest,
            "manifest_digest": self.manifest.digest,
            "acl_version": self.acl_version,
        }
        return "sha256:" + H_A("compiler-identity", canonical_bytes(body)).hex()

    def compile(self, template: dict, params: dict) -> dict:
        # ─── template structural validation ─────────────────
        if not isinstance(template, dict):
            raise AuthoringError("E-META-18", "template must be a dict")

        tid = template.get("template_id")
        if not isinstance(tid, str) or not tid:
            raise AuthoringError("E-META-18", "template_id missing or empty")

        tpl_acl = template.get("acl_version")
        if tpl_acl != self.acl_version:
            raise AuthoringError(
                "E-META-14",
                f"template.acl_version {tpl_acl!r} != compiler {self.acl_version!r}")

        declared = template.get("declared_params")
        if not isinstance(declared, list):
            raise AuthoringError("E-META-18", "declared_params must be a list")
        if not all(isinstance(x, str) for x in declared):
            raise AuthoringError("E-META-18", "declared_params entries must be strings")
        declared_set = set(declared)

        required = template.get("required_params", [])
        if not isinstance(required, list):
            raise AuthoringError("E-META-18", "required_params must be a list")
        if not all(isinstance(x, str) for x in required):
            raise AuthoringError("E-META-18", "required_params entries must be strings")
        required_set = set(required)
        if not required_set.issubset(declared_set):
            extra = required_set - declared_set
            raise AuthoringError(
                "E-META-18",
                f"required_params not subset of declared: {sorted(extra)}")

        purity = template.get("purity")
        if purity != "PURE":
            raise AuthoringError(
                "E-META-21",
                f"purity must be PURE, got {purity!r}")

        # forbidden_env declared but not read (defensive check)
        fe = template.get("forbidden_env", [])
        if not isinstance(fe, list):
            raise AuthoringError("E-META-18", "forbidden_env must be a list")
        # We do not import os; the compile call literally cannot read env.

        # ─── parameters validation (I18) ────────────────────
        if not isinstance(params, dict):
            raise AuthoringError("E-META-18", "params must be a dict")
        for k in params:
            if not isinstance(k, str):
                raise AuthoringError("E-META-18", "param keys must be strings")
            if k not in declared_set:
                raise AuthoringError(
                    "E-META-18", f"undeclared parameter {k!r}")
        missing = required_set - set(params.keys())
        if missing:
            raise AuthoringError(
                "E-META-18", f"missing required params: {sorted(missing)}")

        # ─── AST validation ─────────────────────────────────
        ast = template.get("ast")
        if not isinstance(ast, dict):
            raise AuthoringError("E-META-18", "ast missing or not a dict")
        try:
            acl_validate(ast)
        except ACLError as e:
            raise AuthoringError(e.code, str(e)[:120])

        # ─── digests ─────────────────────────────────────────
        template_digest = "sha256:" + H_A(
            "template", canonical_bytes(template)).hex()
        parameter_digest = "sha256:" + H_A(
            "parameters", canonical_bytes(params)).hex()
        canonical_ast_digest = "sha256:" + H_A(
            "ast", canonical_bytes(canonical_ast(ast))).hex()

        closure = {
            "template_digest": template_digest,
            "parameter_digest": parameter_digest,
            "compiler_digest": self.code_digest,
            "acl_version": self.acl_version,
            "canonical_ast_digest": canonical_ast_digest,
            "meta_manifest_digest": self.manifest.digest,
        }

        # ─── I20: closure completeness ───────────────────────
        if set(closure.keys()) != REQUIRED_CLOSURE_KEYS:
            raise AuthoringError("E-META-20", "closure keys mismatch")
        for k, v in closure.items():
            if not isinstance(v, str) or not v:
                raise AuthoringError("E-META-20", f"closure field {k!r} empty")

        return closure


def compile_authoring(manifest: Manifest,
                      template: dict,
                      params: dict,
                      acl_version: str = ACL_VERSION) -> dict:
    """Convenience: build a Compiler and compile in one call.

    For repeated compilations, reuse a single Compiler instance to
    amortize construction. This wrapper exists for test ergonomics.
    """
    c = Compiler(manifest=manifest, acl_version=acl_version)
    return c.compile(template, params)


__all__ = [
    "Compiler",
    "AuthoringError",
    "compile_authoring",
    "CODE_VERSION",
    "ACL_VERSION",
]

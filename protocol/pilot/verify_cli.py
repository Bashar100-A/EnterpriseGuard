"""ADIE-PILOT v0.1 — full pipeline verifier (Phase 1.10).

Reads JSON from stdin:
  {
    "certificate_json": "<raw certificate text>",
    "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...",
    "manifest": {...},                        (optional)
    "expected_audience": "com.example.x"      (optional)
  }

Writes canonical JSON to stdout:
  {"status":"VALID","checks":{...}}
  or
  {"status":"INVALID","code":"...","message":"..."}

Pipeline verified:
  1. DCP 2.0 structure (via verify_dcp20)
  2. ClaimRoot recomputation
  3. Binding (audience/purpose/resource/request_hash)
  4. Signature (RS256 over canonical signed_payload)
  5. Authoring closure: 6 keys, digests well-formed
  6. AST canonicalization: canonical_ast_digest recomputed
  7. acl_version constant check
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from protocol.core.domain_hash import H_A
from protocol.core.jcs import canonical_bytes, CanonicalError
from protocol.core.verify_pipeline import verify_dcp20, VerifyError
from protocol.acl.ast import validate as acl_validate, ACLError
from protocol.acl.normalize import canonical_ast
from protocol.authoring.compiler import ACL_VERSION


REQUIRED_AUTHORING_KEYS = frozenset({
    "template_digest",
    "parameter_digest",
    "compiler_digest",
    "acl_version",
    "canonical_ast_digest",
    "meta_manifest_digest",
})

HEX_RE_LEN = 71  # "sha256:" + 64 hex


def _canon_out(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def emit_valid(checks):
    sys.stdout.write(_canon_out({"status": "VALID", "checks": checks}) + "\n")
    return 0


def emit_invalid(code, message=""):
    sys.stdout.write(_canon_out({
        "status": "INVALID", "code": code, "message": message}) + "\n")
    return 1


def _is_sha256(s):
    return (isinstance(s, str)
            and len(s) == HEX_RE_LEN
            and s.startswith("sha256:")
            and all(c in "0123456789abcdef" for c in s[7:]))


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except Exception as e:
        return emit_invalid("E-INPUT", str(e)[:80])

    cert_text = data.get("certificate_json")
    pub_pem = data.get("public_key_pem")
    if not isinstance(cert_text, str) or not isinstance(pub_pem, str):
        return emit_invalid("E-INPUT", "certificate_json/public_key_pem required")

    cert_bytes = cert_text.encode("utf-8")
    pub_bytes = pub_pem.encode("utf-8")

    expectation = None
    if data.get("expected_audience"):
        expectation = {"audience": data["expected_audience"]}

    # ─── step 1–4: DCP 2.0 pipeline ─────────────────
    try:
        verify_dcp20(cert_bytes, pub_bytes, expectation)
    except VerifyError as e:
        return emit_invalid(e.code, str(e)[:120])
    except Exception as e:
        return emit_invalid("E-INTERNAL", str(e)[:120])

    # parse again for authoring checks
    try:
        cert = json.loads(cert_text)
    except Exception as e:
        return emit_invalid("E-CANONICAL", str(e)[:80])

    # ─── step 5: authoring closure ──────────────────
    authoring = cert.get("authoring")
    if not isinstance(authoring, dict):
        return emit_invalid("E-META-20", "authoring missing")
    if set(authoring.keys()) != REQUIRED_AUTHORING_KEYS:
        return emit_invalid("E-META-20", "authoring keys mismatch")
    for k in ("template_digest", "parameter_digest", "compiler_digest",
              "canonical_ast_digest", "meta_manifest_digest"):
        if not _is_sha256(authoring.get(k)):
            return emit_invalid("E-META-20", f"{k} malformed")

    # ─── step 6: acl_version constant ───────────────
    if authoring["acl_version"] != ACL_VERSION:
        return emit_invalid("E-META-14",
                            f"authoring.acl_version != {ACL_VERSION}")

    # ─── step 7: AST canonicalization ───────────────
    policy = cert.get("policy")
    if not isinstance(policy, dict):
        return emit_invalid("E-META-18", "policy missing")
    ast = policy.get("expression")
    if not isinstance(ast, dict):
        return emit_invalid("E-META-18", "policy.expression missing")
    try:
        acl_validate(ast)
    except ACLError as e:
        return emit_invalid(e.code, str(e)[:120])
    expected_ast_digest = "sha256:" + H_A(
        "ast", canonical_bytes(canonical_ast(ast))).hex()
    if expected_ast_digest != authoring["canonical_ast_digest"]:
        return emit_invalid("E-META-20", "canonical_ast_digest mismatch")

    # ─── optional manifest check ────────────────────
    if data.get("manifest") is not None:
        m = data["manifest"]
        expected_md = m.get("expected_digest")
        if expected_md is not None and expected_md != authoring["meta_manifest_digest"]:
            return emit_invalid("E-META-20", "manifest digest mismatch")

    checks = {
        "dcp20": "PASS",
        "claim_root": "PASS",
        "binding": "PASS",
        "signature": "PASS",
        "authoring_closure": "PASS",
        "ast_canonicalization": "PASS",
        "acl_version": "PASS",
    }
    return emit_valid(checks)


if __name__ == "__main__":
    sys.exit(main())

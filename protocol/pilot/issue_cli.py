"""ADIE-PILOT v0.1 — full pipeline issuer (Phase 1.10).

Reads JSON from stdin:
  {
    "manifest": {...},
    "template": {...},
    "params": {...},
    "claim_id": "cert-001",
    "issuer_did": "did:adie:issuer-001",
    "request": {...},
    "output": {...},
    "private_key_pem": "-----BEGIN ..."
  }

Writes JSON certificate to stdout.

Pipeline:
  Template + Params -> Compiler.compile -> AClosure
  AST embedded in policy.expression
  AClosure embedded in authoring
  issue_dcp20 -> full DCP 2.0 certificate
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from protocol.meta.core import Manifest, Universe
from protocol.authoring.compiler import Compiler, AuthoringError
from protocol.core.verify_pipeline import issue_dcp20
from protocol.core.binding import request_hash


def build_manifest(m_dict):
    u_dict = m_dict.get("universe") or {}
    u = Universe(
        acl_versions=u_dict.get("acl_versions", []),
        template_ids=u_dict.get("template_ids", []),
        rewrite_ids=u_dict.get("rewrite_ids", []),
        registry_namespaces=u_dict.get("registry_namespaces", []),
        algorithms=u_dict.get("algorithms", []),
        compat_relations=u_dict.get("compat_relations", []),
    )
    return Manifest(
        epoch=int(m_dict.get("epoch", 1)),
        prev_epoch=int(m_dict.get("prev_epoch", 0)),
        universe=u,
        threshold_k=int(m_dict.get("threshold_k", 1)),
        threshold_n=int(m_dict.get("threshold_n", 1)),
        signatures=list(m_dict.get("signatures", ["s1"])),
    )


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except Exception as e:
        sys.stderr.write(f"E-INPUT\n")
        return 2

    try:
        manifest = build_manifest(data["manifest"])
        compiler = Compiler(
            manifest=manifest,
            acl_version=data.get("acl_version", "0.1"),
        )
        closure = compiler.compile(data["template"], data["params"])
    except AuthoringError as e:
        sys.stderr.write(f"{e.code}\n")
        return 1
    except KeyError as e:
        sys.stderr.write(f"E-INPUT: missing {e}\n")
        return 2

    request = data["request"]
    request_h = request_hash(request)

    binding = {
        "audience": data.get("audience", "com.example.deployment"),
        "purpose": int(data.get("purpose", 7)),
        "resource": data.get("resource",
                              "model://sha256:" + "a" * 64),
        "request_hash": request_h,
        "nonce": data.get("nonce", "a" * 32),
        "certificate_id": data["claim_id"],
    }

    fields = {
        "issuer": {
            "did": data.get("issuer_did", "did:adie:issuer-001"),
            "key_id": closure["compiler_digest"],
        },
        "subject": {"model_id": data.get("model_id", "unknown")},
        "binding": binding,
        "request": request,
        "context": data.get("context", {"locale": "en"}),
        "policy": {
            "id": data.get("policy_id", "credit-risk"),
            "version": data.get("policy_version", "7"),
            "expression": data["template"]["ast"],
        },
        "model": data.get("model", {"id": "model-v1"}),
        "data": data.get("data", {"commitment": "sha256:" + "c" * 64}),
        "runtime": data.get("runtime", {"measurement": "sha256:" + "d" * 64}),
        "output": data["output"],
        "temporal": {"issued_at": "2026-10-06T00:00:00Z"},
        "evidence": {"attestations": []},
        "authoring": closure,
    }

    cert_bytes = issue_dcp20(fields,
                              data["private_key_pem"].encode("utf-8"),
                              data["claim_id"])
    sys.stdout.buffer.write(cert_bytes)
    if not cert_bytes.endswith(b"\n"):
        sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""ADIE-AUTHORING v0.1 — Python CLI wrapper.

Reads JSON from stdin:
  {
    "manifest": {epoch, prev_epoch, universe:{...}, threshold_k, threshold_n, signatures},
    "template": {...},
    "params": {...},
    "acl_version": "0.1"
  }

Writes canonical JSON closure to stdout. Errors to stderr.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from protocol.meta.core import Manifest, Universe
from protocol.authoring.compiler import Compiler


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception as e:
        sys.stderr.write(f"E-INPUT: {e}\n")
        return 2

    m_dict = data.get("manifest") or {}
    u_dict = m_dict.get("universe") or {}

    u = Universe(
        acl_versions=u_dict.get("acl_versions", []),
        template_ids=u_dict.get("template_ids", []),
        rewrite_ids=u_dict.get("rewrite_ids", []),
        registry_namespaces=u_dict.get("registry_namespaces", []),
        algorithms=u_dict.get("algorithms", []),
        compat_relations=u_dict.get("compat_relations", []),
    )
    m = Manifest(
        epoch=int(m_dict.get("epoch", 1)),
        prev_epoch=int(m_dict.get("prev_epoch", 0)),
        universe=u,
        threshold_k=int(m_dict.get("threshold_k", 1)),
        threshold_n=int(m_dict.get("threshold_n", 1)),
        signatures=list(m_dict.get("signatures", ["s1"])),
    )

    from protocol.authoring.compiler import AuthoringError

    try:
        acl_version = data.get("acl_version", "0.1")
        c = Compiler(manifest=m, acl_version=acl_version)
        closure = c.compile(data["template"], data["params"])
    except AuthoringError as e:
        sys.stderr.write(f"{e.code}\n")
        return 1

    sys.stdout.write(
        json.dumps(closure, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

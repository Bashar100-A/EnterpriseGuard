"""ADIE-FUZZ v0.1 — Authoring Python fuzzer (Phase 1.11)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from protocol.meta.core import Manifest, Universe
from protocol.authoring.compiler import Compiler, AuthoringError
from protocol.fuzz.generator import rand_template, rand_params


MANIFEST_DICT = {
    "epoch": 1, "prev_epoch": 0,
    "universe": {
        "acl_versions": ["0.1"],
        "template_ids": ["T1", "T2", "T3", "T4"],
        "rewrite_ids": ["R1"],
        "registry_namespaces": ["main"],
        "algorithms": ["RS256"],
        "compat_relations": ["EXACT"],
    },
    "threshold_k": 1, "threshold_n": 1, "signatures": ["s1"],
}


def build_manifest():
    u = MANIFEST_DICT["universe"]
    universe = Universe(
        acl_versions=u["acl_versions"],
        template_ids=u["template_ids"],
        rewrite_ids=u["rewrite_ids"],
        registry_namespaces=u["registry_namespaces"],
        algorithms=u["algorithms"],
        compat_relations=u["compat_relations"],
    )
    return Manifest(
        epoch=MANIFEST_DICT["epoch"],
        prev_epoch=MANIFEST_DICT["prev_epoch"],
        universe=universe,
        threshold_k=MANIFEST_DICT["threshold_k"],
        threshold_n=MANIFEST_DICT["threshold_n"],
        signatures=MANIFEST_DICT["signatures"],
    )


def run(seed, budget):
    import random
    rng = random.Random(seed)
    manifest = build_manifest()
    compiler = Compiler(manifest=manifest, acl_version="0.1")

    out = []
    for i in range(budget):
        template = rand_template(rng)
        params = rand_params(rng, template)
        try:
            closure = compiler.compile(template, params)
            out.append({"i": i, "kind": "ok", "closure": closure})
        except AuthoringError as e:
            out.append({"i": i, "kind": "err", "code": e.code})
        except Exception as e:
            out.append({"i": i, "kind": "err", "code": f"EXC:{type(e).__name__}"})
    return out


if __name__ == "__main__":
    import json
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    print(json.dumps(run(seed, budget), ensure_ascii=False))

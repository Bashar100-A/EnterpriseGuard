"""ADIE-FUZZ v0.1 — ACL Python fuzzer (Phase 1.11)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from protocol.acl.ast import ACLError
from protocol.acl.eval import eval_checked
from protocol.acl.normalize import canonical_bytes, canonical_ast
from protocol.fuzz.generator import rand_expr, rand_state


def run(seed, budget):
    import random
    rng = random.Random(seed)

    results = []
    for i in range(budget):
        expr = rand_expr(rng, 0, 3)
        state = rand_state(rng)
        try:
            verdict = eval_checked(expr, state)
            norm = canonical_bytes(canonical_ast(expr)).decode("utf-8")
            results.append({
                "i": i, "verdict": verdict, "normalized": norm, "err": None
            })
        except ACLError as e:
            results.append({
                "i": i, "verdict": None, "normalized": None, "err": e.code
            })
    return results


if __name__ == "__main__":
    import json
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    print(json.dumps(run(seed, budget), ensure_ascii=False))

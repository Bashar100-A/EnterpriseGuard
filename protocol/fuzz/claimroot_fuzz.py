"""ADIE-FUZZ v0.1 — ClaimRoot Python fuzzer (Phase 1.11)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from protocol.core.claim_root import claim_root_hex
from protocol.fuzz.generator import rand_fields


def run(seed, budget):
    import random
    rng = random.Random(seed)
    out = []
    for i in range(budget):
        fields = rand_fields(rng)
        try:
            root = claim_root_hex(fields)
        except Exception as e:
            root = f"ERR:{type(e).__name__}"
        out.append({"i": i, "root": root})
    return out


if __name__ == "__main__":
    import json
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    print(json.dumps(run(seed, budget), ensure_ascii=False))

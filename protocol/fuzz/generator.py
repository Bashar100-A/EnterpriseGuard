"""ADIE-FUZZ v0.1 — deterministic random generators (Phase 1.11).

All generators take a seed and are reproducible.
No time, no /dev/urandom.
"""
import random


# ─── ACL AST generation ─────────────────────────────────────
ACL_OPS = ["TRUE", "FALSE", "NOT", "AND", "OR",
           "EQ", "NEQ", "LT", "LTE", "GT", "GTE", "EXISTS"]

TERMS = ["INT", "STR", "FIELD"]


def rand_int(rng, lo=-100, hi=100):
    return rng.randint(lo, hi)


def rand_str(rng, maxlen=8):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    n = rng.randint(0, maxlen)
    return "".join(rng.choice(alphabet) for _ in range(n))


def rand_term(rng):
    t = rng.choice(TERMS)
    if t == "INT":
        return {"t": "INT", "v": rand_int(rng)}
    if t == "STR":
        return {"t": "STR", "v": rand_str(rng)}
    # FIELD
    path = ".".join(rand_str(rng, 4) for _ in range(rng.randint(1, 3)))
    return {"t": "FIELD", "path": path or "x"}


def rand_expr(rng, depth=0, max_depth=3):
    if depth >= max_depth:
        return rng.choice([{"op": "TRUE"}, {"op": "FALSE"}])
    op = rng.choice(ACL_OPS)
    if op in ("TRUE", "FALSE"):
        return {"op": op}
    if op == "NOT":
        return {"op": "NOT", "arg": rand_expr(rng, depth + 1, max_depth)}
    if op in ("AND", "OR"):
        n = rng.randint(1, 3)
        return {"op": op, "args": [rand_expr(rng, depth + 1, max_depth)
                                    for _ in range(n)]}
    if op in ("EQ", "NEQ", "LT", "LTE", "GT", "GTE"):
        return {"op": op, "args": [rand_term(rng), rand_term(rng)]}
    if op == "EXISTS":
        return {"op": "EXISTS",
                "path": ".".join(rand_str(rng, 4) for _ in range(rng.randint(1, 3))) or "x"}
    return {"op": "TRUE"}


def rand_state(rng, max_keys=5):
    """Random nested dict with str keys and int/str/bool values."""
    out = {}
    for _ in range(rng.randint(0, max_keys)):
        k = rand_str(rng, 5) or "k"
        r = rng.random()
        if r < 0.5:
            out[k] = rand_int(rng)
        elif r < 0.8:
            out[k] = rand_str(rng)
        else:
            out[k] = rng.choice([True, False])
    return out


# ─── ClaimRoot field generation ─────────────────────────────
FIELD_NAMES_13 = ["issuer", "subject", "request", "context", "policy",
                  "model", "data", "runtime", "output", "binding",
                  "temporal", "evidence", "authoring"]


def rand_field_value(rng):
    r = rng.random()
    if r < 0.3:
        return None
    if r < 0.5:
        return {"k": rand_str(rng)}
    if r < 0.7:
        return [rand_int(rng) for _ in range(rng.randint(0, 3))]
    if r < 0.9:
        return {"nested": {"x": rand_int(rng), "y": rand_str(rng)}}
    return {"a": 1, "b": "two", "c": True}


def rand_fields(rng):
    """Return dict with subset of 13 fields, each possibly None or present."""
    out = {}
    for name in FIELD_NAMES_13:
        r = rng.random()
        if r < 0.15:
            continue  # ABSENT
        out[name] = rand_field_value(rng)  # None => NULL, else PRESENT
    return out


# ─── Template + params generation ───────────────────────────
def rand_template(rng):
    n_declared = rng.randint(0, 4)
    declared = [f"p{i}" for i in range(n_declared)]
    if declared:
        n_required = rng.randint(0, len(declared))
        required = rng.sample(declared, n_required)
    else:
        required = []
    return {
        "template_id": "T" + rand_str(rng, 4),
        "acl_version": "0.1",
        "declared_params": declared,
        "required_params": required,
        "purity": "PURE",
        "ast": rand_expr(rng, 0, 2),
    }


def rand_params(rng, template, inject_error=0.2):
    """Generate params dict, sometimes with undeclared/missing keys."""
    declared = template["declared_params"]
    required = template["required_params"]
    params = {}
    for k in declared:
        if rng.random() < 0.7:
            params[k] = rng.choice([rand_int(rng), rand_str(rng), True])
    # inject error
    if rng.random() < inject_error:
        if rng.random() < 0.5:
            params["undeclared_" + rand_str(rng, 3)] = rand_int(rng)
        else:
            for k in required:
                params.pop(k, None)
    return params

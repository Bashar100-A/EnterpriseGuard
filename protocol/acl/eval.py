"""ADIE-ACL v0.1 — Kleene three-valued evaluator."""
from .ast import ACLError, validate, MAX_DEPTH

PASS = "PASS"; FAIL = "FAIL"; UNKNOWN = "UNKNOWN"

def _get(s, p):
    c = s
    for k in p.split("."):
        if not isinstance(c, dict) or k not in c:
            return False, None
        c = c[k]
    return True, c

def _knot(v): return {PASS:FAIL, FAIL:PASS, UNKNOWN:UNKNOWN}[v]
def _kand(vs):
    if any(v==FAIL for v in vs): return FAIL
    if all(v==PASS for v in vs): return PASS
    return UNKNOWN
def _kor(vs):
    if any(v==PASS for v in vs): return PASS
    if all(v==FAIL for v in vs): return FAIL
    return UNKNOWN

def _et(t, s):
    k = t["t"]
    if k == "FIELD": return _get(s, t["path"])
    if k in ("INT","STR","BOOL"): return True, t["v"]
    raise ACLError("E202_MALFORMED_AST", f"unknown term {k!r}")

def eval_expr(e, s, depth=0):
    if depth > MAX_DEPTH:
        raise ACLError("E208_NESTED_TOO_DEEP", str(depth))
    if not isinstance(e, dict) or "op" not in e:
        raise ACLError("E202_MALFORMED_AST", "missing op")
    op = e["op"]
    if op == "TRUE":  return PASS
    if op == "FALSE": return FAIL
    if op == "NOT":   return _knot(eval_expr(e["arg"], s, depth+1))
    if op == "AND":
        a = e.get("args")
        if not isinstance(a, list) or not a:
            raise ACLError("E209_EMPTY_AND", "AND needs >=1 arg")
        return _kand([eval_expr(x, s, depth+1) for x in a])
    if op == "OR":
        a = e.get("args")
        if not isinstance(a, list) or not a:
            raise ACLError("E210_EMPTY_OR", "OR needs >=1 arg")
        return _kor([eval_expr(x, s, depth+1) for x in a])
    if op in ("EQ","NEQ","LT","LTE","GT","GTE"):
        aok, a = _et(e["args"][0], s)
        bok, b = _et(e["args"][1], s)
        if not aok or not bok:
            return UNKNOWN

        # Type check FIRST (fail-closed, per ACL-0.1 §2.2)
        if type(a) is not type(b):
            raise ACLError("E200_TYPE_MISMATCH",
                f"{op} on {type(a).__name__}/{type(b).__name__}")

        if op == "EQ":  return PASS if a == b else FAIL
        if op == "NEQ": return PASS if a != b else FAIL

        # LT/LTE/GT/GTE: int or str only
        if isinstance(a, bool) or type(a) not in (int, str):
            raise ACLError("E200_TYPE_MISMATCH",
                f"{op} on {type(a).__name__}")

        cmp = (a > b) - (a < b)
        return {"LT":  PASS if cmp < 0 else FAIL,
                "LTE": PASS if cmp <= 0 else FAIL,
                "GT":  PASS if cmp > 0 else FAIL,
                "GTE": PASS if cmp >= 0 else FAIL}[op]
    if op == "IN":
        ok, v = _et(e["term"], s)
        if not ok: return UNKNOWN
        return PASS if v in e["set"] else FAIL
    if op == "EXISTS":
        f, _ = _get(s, e["path"])
        return PASS if f else FAIL
    raise ACLError("E201_UNKNOWN_OPERATOR", op)

def eval_checked(e, s):
    validate(e)
    return eval_expr(e, s)

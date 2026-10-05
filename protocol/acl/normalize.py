"""ADIE-ACL v0.1 — structural normalization R01-R12."""
import json
from .ast import ACLError, MAX_DEPTH

def _cb(x):
    return json.dumps(x, sort_keys=True, separators=(",",":"),
                      ensure_ascii=False).encode("utf-8")

def normalize(e, depth=0):
    if depth > MAX_DEPTH:
        raise ACLError("E208_NESTED_TOO_DEEP", str(depth))
    if not isinstance(e, dict) or "op" not in e:
        return e
    op = e["op"]
    if op == "NOT":
        i = normalize(e["arg"], depth+1)
        if isinstance(i, dict) and i.get("op") == "NOT":
            return normalize(i["arg"], depth+1)
        return {"op":"NOT","arg":i}
    if op in ("AND","OR"):
        flat = []
        for a in e["args"]:
            n = normalize(a, depth+1)
            if isinstance(n, dict) and n.get("op") == op:
                flat.extend(n["args"])
            else:
                flat.append(n)
        if op == "AND":
            if any(isinstance(x,dict) and x.get("op")=="FALSE" for x in flat):
                return {"op":"FALSE"}
            flat = [x for x in flat
                    if not (isinstance(x,dict) and x.get("op")=="TRUE")]
            if not flat: return {"op":"TRUE"}
        else:
            if any(isinstance(x,dict) and x.get("op")=="TRUE" for x in flat):
                return {"op":"TRUE"}
            flat = [x for x in flat
                    if not (isinstance(x,dict) and x.get("op")=="FALSE")]
            if not flat: return {"op":"FALSE"}
        if len(flat) == 1: return flat[0]
        flat.sort(key=_cb)
        return {"op":op,"args":flat}
    return e

def canonical_ast(e):
    n = normalize(e)
    return json.loads(_cb(n).decode("utf-8"))

def canonical_bytes(e):
    return _cb(canonical_ast(e))

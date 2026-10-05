"""ADIE-ACL v0.1 — AST constructors + validation."""
MAX_DEPTH = 32
ALLOWED_OPS = frozenset({"TRUE","FALSE","NOT","AND","OR",
    "EQ","NEQ","LT","LTE","GT","GTE","IN","EXISTS"})
ALLOWED_TERMS = frozenset({"FIELD","INT","STR","BOOL"})

class ACLError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")

def TRUE():       return {"op":"TRUE"}
def FALSE():      return {"op":"FALSE"}
def NOT(a):       return {"op":"NOT","arg":a}
def AND(*a):      return {"op":"AND","args":list(a)}
def OR(*a):       return {"op":"OR","args":list(a)}
def EQ(a,b):      return {"op":"EQ","args":[a,b]}
def NEQ(a,b):     return {"op":"NEQ","args":[a,b]}
def LT(a,b):      return {"op":"LT","args":[a,b]}
def LTE(a,b):     return {"op":"LTE","args":[a,b]}
def GT(a,b):      return {"op":"GT","args":[a,b]}
def GTE(a,b):     return {"op":"GTE","args":[a,b]}
def IN(t,s):      return {"op":"IN","term":t,"set":list(s)}
def EXISTS(p):    return {"op":"EXISTS","path":p}
def FIELD(p):     return {"t":"FIELD","path":p}
def INT(n):       return {"t":"INT","v":n}
def STR(s):       return {"t":"STR","v":s}
def BOOL(b):      return {"t":"BOOL","v":b}

def validate(e, depth=0):
    if depth > MAX_DEPTH:
        raise ACLError("E208_NESTED_TOO_DEEP", str(depth))
    if not isinstance(e, dict) or "op" not in e:
        raise ACLError("E202_MALFORMED_AST", "missing op")
    op = e["op"]
    if op not in ALLOWED_OPS:
        raise ACLError("E201_UNKNOWN_OPERATOR", op)
    if op in ("TRUE","FALSE"):
        return True
    if op == "NOT":
        if "arg" not in e:
            raise ACLError("E202_MALFORMED_AST", "NOT missing arg")
        return validate(e["arg"], depth+1)
    if op in ("AND","OR"):
        a = e.get("args")
        if not isinstance(a, list) or not a:
            raise ACLError("E209_EMPTY_AND" if op=="AND" else "E210_EMPTY_OR", op)
        for x in a:
            validate(x, depth+1)
        return True
    if op in ("EQ","NEQ","LT","LTE","GT","GTE"):
        a = e.get("args")
        if not isinstance(a, list) or len(a) != 2:
            raise ACLError("E202_MALFORMED_AST", f"{op} needs 2 args")
        for x in a:
            _vt(x)
        return True
    if op == "IN":
        if "term" not in e or "set" not in e:
            raise ACLError("E202_MALFORMED_AST", "IN missing term/set")
        _vt(e["term"])
        if not isinstance(e["set"], list):
            raise ACLError("E202_MALFORMED_AST", "IN.set not list")
        return True
    if op == "EXISTS":
        if not isinstance(e.get("path"), str):
            raise ACLError("E202_MALFORMED_AST", "EXISTS missing path")
        return True
    return True

def _vt(t):
    if not isinstance(t, dict) or "t" not in t:
        raise ACLError("E202_MALFORMED_AST", "term missing t")
    if t["t"] not in ALLOWED_TERMS:
        raise ACLError("E202_MALFORMED_AST", f"unknown term {t['t']!r}")
    if t["t"] == "FIELD" and not isinstance(t.get("path"), str):
        raise ACLError("E202_MALFORMED_AST", "FIELD missing path")
    if t["t"] == "INT":
        v = t.get("v")
        if not isinstance(v, int) or isinstance(v, bool):
            raise ACLError("E211_NON_CANONICAL_INT", repr(v))
    return True

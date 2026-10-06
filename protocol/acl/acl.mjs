/**
 * ADIE-ACL v0.1 — JavaScript mirror of protocol/acl/*.py.
 * Must be byte-identical to Python for: eval verdicts, canonical output.
 */
import { createHash } from 'node:crypto';

const MAX_DEPTH = 32;
const ALLOWED_OPS = new Set([
  "TRUE", "FALSE", "NOT", "AND", "OR",
  "EQ", "NEQ", "LT", "LTE", "GT", "GTE", "IN", "EXISTS",
]);
const ALLOWED_TERMS = new Set(["FIELD", "INT", "STR", "BOOL"]);

const PASS = "PASS", FAIL = "FAIL", UNKNOWN = "UNKNOWN";

class ACLError extends Error {
  constructor(code, msg = "") {
    super(`${code}: ${msg}`);
    this.code = code;
  }
}

function get(state, path) {
  let cur = state;
  for (const part of path.split(".")) {
    if (typeof cur !== "object" || cur === null || !(part in cur))
      return [false, null];
    cur = cur[part];
  }
  return [true, cur];
}

function evalTerm(t, state) {
  if (!t || typeof t !== "object" || !("t" in t))
    throw new ACLError("E202_MALFORMED_AST", "term missing t");
  const k = t.t;
  if (k === "FIELD") return get(state, t.path);
  if (k === "INT") {
    if (!Number.isInteger(t.v))
      throw new ACLError("E211_NON_CANONICAL_INT", String(t.v));
    return [true, t.v];
  }
  if (k === "STR") return [true, t.v];
  if (k === "BOOL") return [true, t.v];
  throw new ACLError("E202_MALFORMED_AST", `unknown term ${k}`);
}

function kNot(v) { return { PASS: FAIL, FAIL: PASS, UNKNOWN: UNKNOWN }[v]; }
function kAnd(vs) {
  if (vs.some(v => v === FAIL)) return FAIL;
  if (vs.every(v => v === PASS)) return PASS;
  return UNKNOWN;
}
function kOr(vs) {
  if (vs.some(v => v === PASS)) return PASS;
  if (vs.every(v => v === FAIL)) return FAIL;
  return UNKNOWN;
}

export function evalExpr(e, state, depth = 0) {
  if (depth > MAX_DEPTH) throw new ACLError("E208_NESTED_TOO_DEEP", String(depth));
  if (!e || typeof e !== "object" || !("op" in e))
    throw new ACLError("E202_MALFORMED_AST", "missing op");
  const op = e.op;
  if (op === "TRUE") return PASS;
  if (op === "FALSE") return FAIL;
  if (op === "NOT") return kNot(evalExpr(e.arg, state, depth + 1));
  if (op === "AND") {
    if (!Array.isArray(e.args) || e.args.length === 0)
      throw new ACLError("E209_EMPTY_AND", "AND needs >=1");
    return kAnd(e.args.map(x => evalExpr(x, state, depth + 1)));
  }
  if (op === "OR") {
    if (!Array.isArray(e.args) || e.args.length === 0)
      throw new ACLError("E210_EMPTY_OR", "OR needs >=1");
    return kOr(e.args.map(x => evalExpr(x, state, depth + 1)));
  }
  if (["EQ","NEQ","LT","LTE","GT","GTE"].includes(op)) {
    const [aOk, a] = evalTerm(e.args[0], state);
    const [bOk, b] = evalTerm(e.args[1], state);
    if (!aOk || !bOk) return UNKNOWN;
    if (typeof a !== typeof b)
      throw new ACLError("E200_TYPE_MISMATCH",
        `${op} on ${typeof a}/${typeof b}`);
    if (op === "EQ") return a === b ? PASS : FAIL;
    if (op === "NEQ") return a !== b ? PASS : FAIL;
    if (typeof a === "boolean" || !["number", "string"].includes(typeof a))
      throw new ACLError("E200_TYPE_MISMATCH", `${op} on ${typeof a}`);
    const cmp = a < b ? -1 : a > b ? 1 : 0;
    return { LT: cmp < 0 ? PASS : FAIL,
             LTE: cmp <= 0 ? PASS : FAIL,
             GT: cmp > 0 ? PASS : FAIL,
             GTE: cmp >= 0 ? PASS : FAIL }[op];
  }
  if (op === "IN") {
    const [ok, v] = evalTerm(e.term, state);
    if (!ok) return UNKNOWN;
    return e.set.includes(v) ? PASS : FAIL;
  }
  if (op === "EXISTS") {
    const [found] = get(state, e.path);
    return found ? PASS : FAIL;
  }
  throw new ACLError("E201_UNKNOWN_OPERATOR", op);
}

function stableStringify(x) {
  if (x === null) return "null";
  if (typeof x === "boolean") return x ? "true" : "false";
  if (typeof x === "number") return JSON.stringify(x);
  if (typeof x === "string") return JSON.stringify(x);
  if (Array.isArray(x)) return "[" + x.map(stableStringify).join(",") + "]";
  if (typeof x === "object") {
    const keys = Object.keys(x).sort();
    return "{" + keys.map(k => JSON.stringify(k) + ":" + stableStringify(x[k])).join(",") + "}";
  }
  throw new Error("unexpected type");
}

export function canonicalBytes(x) {
  return stableStringify(x);
}

export function canonicalAst(e) {
  return JSON.parse(stableStringify(normalize(e)));
}

export function normalize(e, depth = 0) {
  if (depth > MAX_DEPTH) throw new ACLError("E208_NESTED_TOO_DEEP", String(depth));
  if (!e || typeof e !== "object" || !("op" in e)) return e;
  const op = e.op;
  if (op === "NOT") {
    const i = normalize(e.arg, depth + 1);
    if (i && typeof i === "object" && i.op === "NOT")
      return normalize(i.arg, depth + 1);
    return { op: "NOT", arg: i };
  }
  if (op === "AND" || op === "OR") {
    let flat = [];
    for (const a of e.args) {
      const n = normalize(a, depth + 1);
      if (n && typeof n === "object" && n.op === op) flat.push(...n.args);
      else flat.push(n);
    }
    if (op === "AND") {
      if (flat.some(x => x && x.op === "FALSE")) return { op: "FALSE" };
      flat = flat.filter(x => !(x && x.op === "TRUE"));
      if (flat.length === 0) return { op: "TRUE" };
    } else {
      if (flat.some(x => x && x.op === "TRUE")) return { op: "TRUE" };
      flat = flat.filter(x => !(x && x.op === "FALSE"));
      if (flat.length === 0) return { op: "FALSE" };
    }
    if (flat.length === 1) return flat[0];
    flat.sort((a, b) => {
      const ba = canonicalBytes(a), bb = canonicalBytes(b);
      return ba < bb ? -1 : ba > bb ? 1 : 0;
    });
    return { op, args: flat };
  }
  return e;
}

export function validate(e, depth = 0) {
  if (depth > MAX_DEPTH) throw new ACLError("E208_NESTED_TOO_DEEP", String(depth));
  if (!e || typeof e !== "object" || !("op" in e))
    throw new ACLError("E202_MALFORMED_AST", "missing op");
  const op = e.op;
  if (!ALLOWED_OPS.has(op)) throw new ACLError("E201_UNKNOWN_OPERATOR", op);
  if (op === "TRUE" || op === "FALSE") return true;
  if (op === "NOT") return validate(e.arg, depth + 1);
  if (op === "AND" || op === "OR") {
    if (!Array.isArray(e.args) || e.args.length === 0)
      throw new ACLError(op === "AND" ? "E209_EMPTY_AND" : "E210_EMPTY_OR", op);
    for (const x of e.args) validate(x, depth + 1);
    return true;
  }
  if (["EQ","NEQ","LT","LTE","GT","GTE"].includes(op)) {
    if (!Array.isArray(e.args) || e.args.length !== 2)
      throw new ACLError("E202_MALFORMED_AST", `${op} needs 2 args`);
    for (const x of e.args) validateTerm(x);
    return true;
  }
  if (op === "IN") {
    if (!("term" in e) || !("set" in e))
      throw new ACLError("E202_MALFORMED_AST", "IN missing term/set");
    validateTerm(e.term);
    if (!Array.isArray(e.set))
      throw new ACLError("E202_MALFORMED_AST", "IN.set not list");
    return true;
  }
  if (op === "EXISTS") {
    if (typeof e.path !== "string")
      throw new ACLError("E202_MALFORMED_AST", "EXISTS missing path");
    return true;
  }
  return true;
}

function validateTerm(t) {
  if (!t || typeof t !== "object" || !("t" in t))
    throw new ACLError("E202_MALFORMED_AST", "term missing t");
  if (!ALLOWED_TERMS.has(t.t))
    throw new ACLError("E202_MALFORMED_AST", `unknown term ${t.t}`);
  if (t.t === "FIELD" && typeof t.path !== "string")
    throw new ACLError("E202_MALFORMED_AST", "FIELD missing path");
  if (t.t === "INT" && !Number.isInteger(t.v))
    throw new ACLError("E211_NON_CANONICAL_INT", String(t.v));
  return true;
}

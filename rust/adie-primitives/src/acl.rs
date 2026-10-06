//! ADIE-ACL v0.1 — Rust mirror of protocol/acl/*.py.
//! Must match Python byte-for-byte on: eval verdicts, canonical bytes.
use serde_json::{json, Value};
use crate::jcs::canonical_bytes;

const MAX_DEPTH: usize = 32;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Verdict { Pass, Fail, Unknown }

impl Verdict {
    pub fn as_str(&self) -> &'static str {
        match self { Verdict::Pass => "PASS", Verdict::Fail => "FAIL", Verdict::Unknown => "UNKNOWN" }
    }
}

#[derive(Debug)]
pub struct AclError { pub code: String, pub message: String }

impl AclError {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        AclError { code: code.to_string(), message: message.into() }
    }
}

fn fail<T>(code: &str, message: impl Into<String>) -> Result<T, AclError> {
    Err(AclError::new(code, message))
}

fn get_path<'a>(state: &'a Value, path: &str) -> Option<&'a Value> {
    let mut cur = state;
    for part in path.split('.') {
        cur = cur.as_object()?.get(part)?;
    }
    Some(cur)
}

fn type_name(v: &Value) -> &'static str {
    match v {
        Value::Null => "null", Value::Bool(_) => "bool", Value::Number(_) => "int",
        Value::String(_) => "str", Value::Array(_) => "list", Value::Object(_) => "dict",
    }
}

fn eval_term<'a>(t: &'a Value, state: &'a Value) -> Result<Option<&'a Value>, AclError> {
    let obj = t.as_object().ok_or_else(|| AclError::new("E202_MALFORMED_AST", "term not object"))?;
    let kind = obj.get("t").and_then(|v| v.as_str())
        .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "term missing t"))?;
    match kind {
        "FIELD" => {
            let path = obj.get("path").and_then(|v| v.as_str())
                .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "FIELD missing path"))?;
            Ok(get_path(state, path))
        }
        "INT" => {
            let v = obj.get("v").ok_or_else(|| AclError::new("E211_NON_CANONICAL_INT", "missing v"))?;
            if !v.is_i64() && !v.is_u64() {
                return fail("E211_NON_CANONICAL_INT", "not integer");
            }
            Ok(Some(v))
        }
        "STR" => Ok(obj.get("v")),
        "BOOL" => Ok(obj.get("v")),
        _ => fail("E202_MALFORMED_AST", format!("unknown term {}", kind)),
    }
}

fn k_not(v: &Verdict) -> Verdict {
    match v { Verdict::Pass => Verdict::Fail, Verdict::Fail => Verdict::Pass, Verdict::Unknown => Verdict::Unknown }
}
fn k_and(vs: &[Verdict]) -> Verdict {
    if vs.iter().any(|v| *v == Verdict::Fail) { return Verdict::Fail; }
    if vs.iter().all(|v| *v == Verdict::Pass) { return Verdict::Pass; }
    Verdict::Unknown
}
fn k_or(vs: &[Verdict]) -> Verdict {
    if vs.iter().any(|v| *v == Verdict::Pass) { return Verdict::Pass; }
    if vs.iter().all(|v| *v == Verdict::Fail) { return Verdict::Fail; }
    Verdict::Unknown
}

pub fn eval_expr(e: &Value, state: &Value) -> Result<Verdict, AclError> {
    eval_expr_depth(e, state, 0)
}

fn eval_expr_depth(e: &Value, state: &Value, depth: usize) -> Result<Verdict, AclError> {
    if depth > MAX_DEPTH { return fail("E208_NESTED_TOO_DEEP", depth.to_string()); }
    let obj = e.as_object().ok_or_else(|| AclError::new("E202_MALFORMED_AST", "expr not object"))?;
    let op = obj.get("op").and_then(|v| v.as_str())
        .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "expr missing op"))?;

    match op {
        "TRUE" => Ok(Verdict::Pass),
        "FALSE" => Ok(Verdict::Fail),
        "NOT" => {
            let arg = obj.get("arg").ok_or_else(|| AclError::new("E202_MALFORMED_AST", "NOT missing arg"))?;
            Ok(k_not(&eval_expr_depth(arg, state, depth + 1)?))
        }
        "AND" => {
            let args = obj.get("args").and_then(|v| v.as_array())
                .ok_or_else(|| AclError::new("E209_EMPTY_AND", "AND needs args"))?;
            if args.is_empty() { return fail("E209_EMPTY_AND", "empty"); }
            let mut vs = Vec::with_capacity(args.len());
            for a in args { vs.push(eval_expr_depth(a, state, depth + 1)?); }
            Ok(k_and(&vs))
        }
        "OR" => {
            let args = obj.get("args").and_then(|v| v.as_array())
                .ok_or_else(|| AclError::new("E210_EMPTY_OR", "OR needs args"))?;
            if args.is_empty() { return fail("E210_EMPTY_OR", "empty"); }
            let mut vs = Vec::with_capacity(args.len());
            for a in args { vs.push(eval_expr_depth(a, state, depth + 1)?); }
            Ok(k_or(&vs))
        }
        "EQ" | "NEQ" | "LT" | "LTE" | "GT" | "GTE" => {
            let args = obj.get("args").and_then(|v| v.as_array())
                .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "cmp needs args"))?;
            if args.len() != 2 { return fail("E202_MALFORMED_AST", "cmp needs 2 args"); }
            let a = eval_term(&args[0], state)?;
            let b = eval_term(&args[1], state)?;
            let (a, b) = match (a, b) { (Some(x), Some(y)) => (x, y), _ => return Ok(Verdict::Unknown) };
            if type_name(a) != type_name(b) {
                return fail("E200_TYPE_MISMATCH",
                            format!("{} on {}/{}", op, type_name(a), type_name(b)));
            }
            match op {
                "EQ" => Ok(if a == b { Verdict::Pass } else { Verdict::Fail }),
                "NEQ" => Ok(if a != b { Verdict::Pass } else { Verdict::Fail }),
                _ => {
                    let ord = match (a, b) {
                        (Value::Number(x), Value::Number(y)) => {
                            let xi = x.as_i64().ok_or_else(|| AclError::new("E200_TYPE_MISMATCH", "num"))?;
                            let yi = y.as_i64().ok_or_else(|| AclError::new("E200_TYPE_MISMATCH", "num"))?;
                            xi.cmp(&yi)
                        }
                        (Value::String(x), Value::String(y)) => x.cmp(y),
                        _ => return fail("E200_TYPE_MISMATCH", format!("{} on {}", op, type_name(a))),
                    };
                    Ok(match op {
                        "LT" => if ord == std::cmp::Ordering::Less { Verdict::Pass } else { Verdict::Fail },
                        "LTE" => if ord != std::cmp::Ordering::Greater { Verdict::Pass } else { Verdict::Fail },
                        "GT" => if ord == std::cmp::Ordering::Greater { Verdict::Pass } else { Verdict::Fail },
                        "GTE" => if ord != std::cmp::Ordering::Less { Verdict::Pass } else { Verdict::Fail },
                        _ => unreachable!(),
                    })
                }
            }
        }
        "IN" => {
            let term = obj.get("term").ok_or_else(|| AclError::new("E202_MALFORMED_AST", "IN missing term"))?;
            let set = obj.get("set").and_then(|v| v.as_array())
                .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "IN missing set"))?;
            match eval_term(term, state)? {
                None => Ok(Verdict::Unknown),
                Some(val) => Ok(if set.iter().any(|x| x == val) { Verdict::Pass } else { Verdict::Fail }),
            }
        }
        "EXISTS" => {
            let path = obj.get("path").and_then(|v| v.as_str())
                .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "EXISTS missing path"))?;
            Ok(if get_path(state, path).is_some() { Verdict::Pass } else { Verdict::Fail })
        }
        _ => fail("E201_UNKNOWN_OPERATOR", op.to_string()),
    }
}

pub fn normalize(e: &Value) -> Result<Value, AclError> {
    normalize_depth(e, 0)
}

fn normalize_depth(e: &Value, depth: usize) -> Result<Value, AclError> {
    if depth > MAX_DEPTH { return fail("E208_NESTED_TOO_DEEP", depth.to_string()); }
    let obj = match e.as_object() { Some(o) => o, None => return Ok(e.clone()) };
    let op = match obj.get("op").and_then(|v| v.as_str()) { Some(o) => o, None => return Ok(e.clone()) };

    match op {
        "NOT" => {
            let arg = obj.get("arg").ok_or_else(|| AclError::new("E202_MALFORMED_AST", "NOT missing arg"))?;
            let inner = normalize_depth(arg, depth + 1)?;
            if let Some(io) = inner.as_object() {
                if io.get("op").and_then(|v| v.as_str()) == Some("NOT") {
                    return normalize_depth(io.get("arg").unwrap(), depth + 1);
                }
            }
            Ok(json!({"op": "NOT", "arg": inner}))
        }
        "AND" | "OR" => {
            let args = obj.get("args").and_then(|v| v.as_array())
                .ok_or_else(|| AclError::new("E202_MALFORMED_AST", "missing args"))?;
            let mut flat: Vec<Value> = Vec::new();
            for a in args {
                let n = normalize_depth(a, depth + 1)?;
                if let Some(no) = n.as_object() {
                    if no.get("op").and_then(|v| v.as_str()) == Some(op) {
                        if let Some(sub) = no.get("args").and_then(|v| v.as_array()) {
                            flat.extend(sub.iter().cloned());
                            continue;
                        }
                    }
                }
                flat.push(n);
            }
            if op == "AND" {
                if flat.iter().any(|x| x.get("op").and_then(|v| v.as_str()) == Some("FALSE")) {
                    return Ok(json!({"op": "FALSE"}));
                }
                flat.retain(|x| x.get("op").and_then(|v| v.as_str()) != Some("TRUE"));
                if flat.is_empty() { return Ok(json!({"op": "TRUE"})); }
            } else {
                if flat.iter().any(|x| x.get("op").and_then(|v| v.as_str()) == Some("TRUE")) {
                    return Ok(json!({"op": "TRUE"}));
                }
                flat.retain(|x| x.get("op").and_then(|v| v.as_str()) != Some("FALSE"));
                if flat.is_empty() { return Ok(json!({"op": "FALSE"})); }
            }
            if flat.len() == 1 { return Ok(flat.into_iter().next().unwrap()); }
            let mut with_key: Vec<(Vec<u8>, Value)> = Vec::with_capacity(flat.len());
            for v in flat {
                let b = canonical_bytes(&v).map_err(|m| AclError::new("E-INTERNAL", m))?;
                with_key.push((b, v));
            }
            with_key.sort_by(|a, b| a.0.cmp(&b.0));
            let sorted: Vec<Value> = with_key.into_iter().map(|(_, v)| v).collect();
            Ok(json!({"op": op, "args": sorted}))
        }
        _ => Ok(e.clone()),
    }
}

pub fn canonical_bytes_of(e: &Value) -> Result<Vec<u8>, AclError> {
    let n = normalize(e)?;
    canonical_bytes(&n).map_err(|m| AclError::new("E-INTERNAL", m))
}

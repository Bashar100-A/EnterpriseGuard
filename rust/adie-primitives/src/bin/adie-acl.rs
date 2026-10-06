//! adie-acl — eval + normalize CLI.
//! stdin:  {"expr": <ast>, "state": <object>}
//! stdout: {"verdict": "PASS"|"FAIL"|"UNKNOWN"|null, "canon": "<utf8>"|null, "err": "<code>"|null}
use std::io::Read;
use serde_json::{json, Value};
use adie_primitives::acl::{eval_expr, canonical_bytes_of};

fn main() {
    let mut buf = String::new();
    if std::io::stdin().read_to_string(&mut buf).is_err() {
        eprintln!("E-INPUT");
        std::process::exit(2);
    }
    let v: Value = match serde_json::from_str(&buf) {
        Ok(x) => x,
        Err(_) => { eprintln!("E-INPUT"); std::process::exit(2); }
    };
    let expr = v.get("expr").cloned().unwrap_or(Value::Null);
    let state = v.get("state").cloned().unwrap_or_else(|| json!({}));

    let canon = canonical_bytes_of(&expr)
        .ok()
        .and_then(|b| String::from_utf8(b).ok());

    let (verdict, err) = match eval_expr(&expr, &state) {
        Ok(vd) => (Some(vd.as_str().to_string()), None),
        Err(e) => (None, Some(e.code)),
    };

    let out = json!({
        "verdict": verdict,
        "canon": canon,
        "err": err,
    });
    println!("{}", out);
}

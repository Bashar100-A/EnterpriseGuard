//! adie-cbor — CLI for the ADIE CBOR profile (Phase 3, Gate 1, 3A.3).
//!
//! This binary is the Rust-side endpoint for the Python↔Rust
//! differential tests. It exposes cbor::encode and cbor::decode
//! through a small JSON protocol.
//!
//! It does NOT introduce new behavior. It wraps the existing
//! rust/adie-primitives/src/cbor/ module.

use std::io::Read;

use serde_json::{json, Value};

use adie_primitives::cbor::decoder::decode;
use adie_primitives::cbor::encoder::encode;
use adie_primitives::cbor::error::CborError;
use adie_primitives::cbor::value::AdieValue;

fn value_to_json(v: &AdieValue) -> Value {
    match v {
        AdieValue::UInt(n)  => json!({"t": "uint",  "v": n}),
        AdieValue::Int(n)   => json!({"t": "int",   "v": n}),
        AdieValue::Bytes(b) => json!({"t": "bytes", "v": hex_encode(b)}),
        AdieValue::Text(s)  => json!({"t": "text",  "v": s}),
        AdieValue::Bool(b)  => json!({"t": "bool",  "v": b}),
        AdieValue::Null     => json!({"t": "null"}),
        AdieValue::Array(items) => {
            let arr: Vec<Value> = items.iter().map(value_to_json).collect();
            json!({"t": "array", "v": arr})
        }
        AdieValue::Map(entries) => {
            let pairs: Vec<Value> = entries.iter()
                .map(|(k, v)| json!([k, value_to_json(v)]))
                .collect();
            json!({"t": "map", "v": pairs})
        }
    }
}

fn json_to_value(v: &Value) -> Result<AdieValue, String> {
    let obj = v.as_object().ok_or("value must be object")?;
    let t = obj.get("t").and_then(|x| x.as_str()).ok_or("missing t")?;
    match t {
        "uint" => {
            let n = obj.get("v").and_then(|x| x.as_u64()).ok_or("uint v")?;
            Ok(AdieValue::UInt(n))
        }
        "int" => {
            let n = obj.get("v").and_then(|x| x.as_i64()).ok_or("int v")?;
            Ok(AdieValue::Int(n))
        }
        "bytes" => {
            let h = obj.get("v").and_then(|x| x.as_str()).ok_or("bytes v")?;
            let b = hex_decode(h).map_err(|e| format!("hex: {}", e))?;
            Ok(AdieValue::Bytes(b))
        }
        "text" => {
            let s = obj.get("v").and_then(|x| x.as_str()).ok_or("text v")?;
            Ok(AdieValue::Text(s.to_string()))
        }
        "bool" => {
            let b = obj.get("v").and_then(|x| x.as_bool()).ok_or("bool v")?;
            Ok(AdieValue::Bool(b))
        }
        "null" => Ok(AdieValue::Null),
        "array" => {
            let arr = obj.get("v").and_then(|x| x.as_array()).ok_or("array v")?;
            let mut out = Vec::with_capacity(arr.len());
            for item in arr {
                out.push(json_to_value(item)?);
            }
            Ok(AdieValue::Array(out))
        }
        "map" => {
            let arr = obj.get("v").and_then(|x| x.as_array()).ok_or("map v")?;
            let mut out = Vec::with_capacity(arr.len());
            for pair in arr {
                let p = pair.as_array().ok_or("pair not array")?;
                if p.len() != 2 { return Err("pair must be [k,v]".into()); }
                let k = p[0].as_u64().ok_or("key not u64")?;
                let v = json_to_value(&p[1])?;
                out.push((k, v));
            }
            Ok(AdieValue::Map(out))
        }
        other => Err(format!("unknown type tag {:?}", other)),
    }
}

fn hex_encode(b: &[u8]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}

fn hex_decode(h: &str) -> Result<Vec<u8>, String> {
    let bytes = h.as_bytes();
    if bytes.len() % 2 != 0 { return Err("odd hex length".into()); }
    let mut out = Vec::with_capacity(bytes.len() / 2);
    for i in (0..bytes.len()).step_by(2) {
        let hi = (bytes[i] as char).to_digit(16).ok_or("bad hex")? as u8;
        let lo = (bytes[i + 1] as char).to_digit(16).ok_or("bad hex")? as u8;
        out.push((hi << 4) | lo);
    }
    Ok(out)
}

fn main() {
    let mut buf = String::new();
    if std::io::stdin().read_to_string(&mut buf).is_err() {
        eprintln!("E-INPUT");
        std::process::exit(2);
    }
    let input: Value = match serde_json::from_str(&buf) {
        Ok(v) => v,
        Err(e) => { eprintln!("E-JSON: {}", e); std::process::exit(2); }
    };

    let op = input.get("op").and_then(|v| v.as_str()).unwrap_or("");

    match op {
        "encode" => {
            let val = match input.get("value") {
                Some(v) => v,
                None => { eprintln!("missing value"); std::process::exit(2); }
            };
            let av = match json_to_value(val) {
                Ok(v) => v,
                Err(e) => { eprintln!("E-VALUE: {}", e); std::process::exit(2); }
            };
            match encode(&av) {
                Ok(bytes) => {
                    let out = json!({"cbor_hex": hex_encode(&bytes)});
                    println!("{}", out);
                }
                Err(e) => {
                    let out = json!({"error": e.code(), "detail": e.to_string()});
                    println!("{}", out);
                    std::process::exit(1);
                }
            }
        }
        "decode" => {
            let h = input.get("cbor_hex").and_then(|v| v.as_str()).unwrap_or("");
            let bytes = match hex_decode(h) {
                Ok(b) => b,
                Err(e) => { eprintln!("E-HEX: {}", e); std::process::exit(2); }
            };
            match decode(&bytes) {
                Ok(av) => {
                    let out = json!({"value": value_to_json(&av)});
                    println!("{}", out);
                }
                Err(e) => {
                    let out = json!({"error": e.code(), "detail": e.to_string()});
                    println!("{}", out);
                    std::process::exit(1);
                }
            }
        }
        _ => { eprintln!("unknown op: {}", op); std::process::exit(2); }
    }
}

// Silence the unused-import warning if CborError is only used for .code()
#[allow(dead_code)]
fn _touch(_: CborError) {}

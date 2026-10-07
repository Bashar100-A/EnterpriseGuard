//! adie-cbor-envelope — B+ envelope endpoint (Phase 3, Gate 1, 3A.5-B+).
//!
//! stdin:  {"op":"build","certificate_json":"<json>"}
//! stdin:  {"op":"parse","envelope_hex":"<hex>"}
//! stdout: {"envelope_hex":"..."} | {"certificate_json":"..."} | {"error":"E_.."}

use std::io::Read;
use serde_json::{json, Value};
use adie_primitives::cbor::envelope::{build_envelope, parse_envelope};
use adie_primitives::hex;

fn main() {
    let mut buf = String::new();
    if std::io::stdin().read_to_string(&mut buf).is_err() {
        println!("{}", json!({"error":"E-INPUT"}));
        return;
    }
    let req: Value = match serde_json::from_str(&buf) {
        Ok(v) => v,
        Err(e) => { println!("{}", json!({"error":"E-JSON","detail":e.to_string()})); return; }
    };
    let op = req.get("op").and_then(|v| v.as_str());
    match op {
        Some("build") => {
            let cert = match req.get("certificate_json").and_then(|v| v.as_str()) {
                Some(s) => s,
                None => { println!("{}", json!({"error":"E-MISSING-CERT"})); return; }
            };
            match build_envelope(cert) {
                Ok(bytes) => println!("{}", json!({"envelope_hex": hex::encode(&bytes)})),
                Err(e) => println!("{}", json!({"error": e.code(), "detail": e.to_string()})),
            }
        }
        Some("parse") => {
            let hexs = match req.get("envelope_hex").and_then(|v| v.as_str()) {
                Some(s) => s,
                None => { println!("{}", json!({"error":"E-MISSING-HEX"})); return; }
            };
            let bytes = match hex_decode(hexs) {
                Ok(b) => b,
                Err(_) => { println!("{}", json!({"error":"E-HEX"})); return; }
            };
            match parse_envelope(&bytes) {
                Ok(json_str) => println!("{}", json!({"certificate_json": json_str})),
                Err(e) => println!("{}", json!({"error": e.code(), "detail": e.to_string()})),
            }
        }
        Some("parse_batch") => {
            let arr = match req.get("envelopes_hex").and_then(|v| v.as_array()) {
                Some(a) => a,
                None => { println!("{}", json!({"error":"E-MISSING-ARRAY"})); return; }
            };
            let mut results = Vec::with_capacity(arr.len());
            for h in arr {
                let hx = match h.as_str() {
                    Some(s) => s,
                    None => { results.push(json!({"error":"E-NOT-STR"})); continue; }
                };
                let bytes = match hex_decode(hx) {
                    Ok(b) => b,
                    Err(_) => { results.push(json!({"error":"E-HEX"})); continue; }
                };
                match parse_envelope(&bytes) {
                    Ok(json_str) => results.push(json!({"certificate_json": json_str})),
                    Err(e) => results.push(json!({"error": e.code(), "detail": e.to_string()})),
                }
            }
            println!("{}", json!({"results": results}));
        }
        _ => println!("{}", json!({"error":"E-OP"})),
    }
}

fn hex_decode(s: &str) -> Result<Vec<u8>, ()> {
    if s.len() % 2 != 0 { return Err(()); }
    let b = s.as_bytes();
    let mut out = Vec::with_capacity(b.len()/2);
    for i in (0..b.len()).step_by(2) {
        let hi = (b[i] as char).to_digit(16).ok_or(())? as u8;
        let lo = (b[i+1] as char).to_digit(16).ok_or(())? as u8;
        out.push((hi<<4) | lo);
    }
    Ok(out)
}

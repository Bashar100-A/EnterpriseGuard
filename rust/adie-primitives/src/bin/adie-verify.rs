//! adie-verify — Rust semantic verifier for DCP 2.0 certificates.
//! Reads JSON from stdin:
//!   {"certificate_json": "...", "expected_audience": "..." (optional)}
//! Writes canonical JSON to stdout.
use std::io::Read;
use serde_json::Value;
use adie_primitives::verifier::{verify_semantic, emit_valid_json, emit_invalid_json};

fn main() {
    let mut buf = String::new();
    if std::io::stdin().read_to_string(&mut buf).is_err() {
        eprintln!("E-INPUT");
        std::process::exit(2);
    }
    let input: Value = match serde_json::from_str(&buf) {
        Ok(v) => v,
        Err(_) => { eprintln!("E-INPUT"); std::process::exit(2); }
    };

    let cert_text = match input.get("certificate_json").and_then(|v| v.as_str()) {
        Some(s) => s,
        None => { eprintln!("E-INPUT: certificate_json required"); std::process::exit(2); }
    };

    let cert: Value = match serde_json::from_str(cert_text) {
        Ok(v) => v,
        Err(_) => {
            println!("{{\"code\":\"E-CANONICAL\",\"message\":\"E-CANONICAL: malformed JSON\",\"status\":\"INVALID\"}}");
            std::process::exit(1);
        }
    };

    let expected_audience = input.get("expected_audience").and_then(|v| v.as_str());

    match verify_semantic(&cert, expected_audience) {
        Ok(checks) => { println!("{}", emit_valid_json(&checks)); }
        Err(e) => {
            println!("{}", emit_invalid_json(&e));
            std::process::exit(1);
        }
    }
}

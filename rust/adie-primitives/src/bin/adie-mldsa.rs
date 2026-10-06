//! adie-mldsa — CLI for ML-DSA-65 operations (Phase 2, Block D.1).
//! JSON in, JSON out.

use std::io::Read;
use serde_json::{json, Value};
use adie_primitives::{hex, mldsa};

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

    let get_hex = |key: &str| -> Result<Vec<u8>, String> {
        let s = input.get(key).and_then(|v| v.as_str())
            .ok_or_else(|| format!("missing {}", key))?;
        hex::decode(s).map_err(|e| format!("{}: {}", key, e))
    };

    match op {
        "keygen" => {
            let seed_bytes = match get_hex("seed_hex") {
                Ok(b) => b,
                Err(e) => { eprintln!("{}", e); std::process::exit(2); }
            };
            let seed_arr: [u8; 32] = match seed_bytes.try_into() {
                Ok(a) => a,
                Err(_) => { eprintln!("seed must be 32 bytes"); std::process::exit(2); }
            };
            match mldsa::keygen_from_seed(&seed_arr) {
                Ok(pk) => println!("{}", json!({
                    "public_key_hex": hex::encode(&pk),
                    "public_key_len": pk.len(),
                })),
                Err(e) => { eprintln!("E: {}", e); std::process::exit(1); }
            }
        }
        "sign" => {
            let seed_bytes = match get_hex("seed_hex") {
                Ok(b) => b,
                Err(e) => { eprintln!("{}", e); std::process::exit(2); }
            };
            let tbs = match get_hex("tbs_hex") {
                Ok(b) => b,
                Err(e) => { eprintln!("{}", e); std::process::exit(2); }
            };
            let seed_arr: [u8; 32] = match seed_bytes.try_into() {
                Ok(a) => a,
                Err(_) => { eprintln!("seed must be 32 bytes"); std::process::exit(2); }
            };
            match mldsa::sign_deterministic(&seed_arr, &tbs) {
                Ok(sig) => println!("{}", json!({
                    "signature_hex": hex::encode(&sig),
                    "signature_len": sig.len(),
                })),
                Err(e) => { eprintln!("E: {}", e); std::process::exit(1); }
            }
        }
        "verify" => {
            let pk = match get_hex("public_key_hex") { Ok(b) => b, Err(e) => { eprintln!("{}", e); std::process::exit(2); } };
            let tbs = match get_hex("tbs_hex") { Ok(b) => b, Err(e) => { eprintln!("{}", e); std::process::exit(2); } };
            let sig = match get_hex("signature_hex") { Ok(b) => b, Err(e) => { eprintln!("{}", e); std::process::exit(2); } };
            match mldsa::verify(&pk, &tbs, &sig) {
                Ok(v) => println!("{}", json!({"valid": v})),
                Err(e) => { eprintln!("E: {}", e); std::process::exit(1); }
            }
        }
        _ => { eprintln!("E: unknown op {:?}", op); std::process::exit(2); }
    }
}

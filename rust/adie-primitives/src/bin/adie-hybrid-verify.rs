//! adie-hybrid-verify — full DCP 2.1 hybrid verification (Phase 3, Gate 0).
//!
//! Reads JSON from stdin, writes canonical JSON to stdout.
//! Matches Python's `verify_hybrid` semantics byte-for-byte.
//!
//! Input:
//!   {
//!     "cert": { ...DCP 2.1 certificate with "signatures" array... },
//!     "public_keys": {
//!       "RS256":      "<PEM string>",
//!       "ML-DSA-65":  "<hex-encoded 1952-byte raw pk>"
//!     },
//!     "required_algs": ["RS256", "ML-DSA-65"],
//!     "expected_audience": "com.example.deployment"   (optional)
//!   }
//!
//! Output (VALID):
//!   {"status":"VALID","checks":{"RS256":"PASS","ML-DSA-65":"PASS"}}
//!
//! Output (INVALID):
//!   {"status":"INVALID","code":"E_SIGNATURE_HYBRID_INVALID","message":"..."}

use std::collections::BTreeMap;
use std::io::Read;

use serde_json::{json, Value};

use adie_primitives::hex;
use adie_primitives::mldsa;
use adie_primitives::rsa_verify;

const ALLOWED_ALGS: &[&str] = &["RS256", "ML-DSA-65"];

fn take_chars(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

fn emit_valid(checks: &BTreeMap<String, String>) -> i32 {
    let out = json!({"status": "VALID", "checks": checks});
    println!("{}", serde_json::to_string(&out).unwrap_or_default());
    0
}

fn emit_invalid(code: &str, message: &str) -> i32 {
    let out = json!({
        "status": "INVALID",
        "code": code,
        "message": message,
    });
    println!("{}", serde_json::to_string(&out).unwrap_or_default());
    1
}


// Compute key_id for RS256 public key (SPKI DER).
fn rs256_key_id_from_pem(pub_pem: &[u8]) -> Result<String, String> {
    use rsa::pkcs8::DecodePublicKey;
    use sha2::{Digest, Sha256};
    let pubkey = rsa::RsaPublicKey::from_public_key_pem(
        std::str::from_utf8(pub_pem).map_err(|e| format!("utf8: {}", e))?,
    ).map_err(|e| format!("pem: {}", e))?;
    use rsa::pkcs8::EncodePublicKey;
    let der = pubkey.to_public_key_der()
        .map_err(|e| format!("der: {}", e))?;
    let digest = Sha256::digest(der.as_bytes());
    Ok(format!("sha256:{}", hex::encode(&digest)))
}

// Compute key_id for ML-DSA-65 raw pk (1952 bytes).
fn mldsa65_key_id_from_raw(pk_raw: &[u8]) -> Result<String, String> {
    use sha2::{Digest, Sha256};
    let digest = Sha256::digest(pk_raw);
    Ok(format!("sha256:{}", hex::encode(&digest)))
}

fn main() {
    let mut buf = String::new();
    if std::io::stdin().read_to_string(&mut buf).is_err() {
        std::process::exit(emit_invalid("E-INPUT", "stdin read failed"));
    }
    let input: Value = match serde_json::from_str(&buf) {
        Ok(v) => v,
        Err(e) => std::process::exit(emit_invalid("E-INPUT", &e.to_string()[..e.to_string().len().min(80)])),
    };

    // cert
    let cert = match input.get("cert").and_then(|v| v.as_object()) {
        Some(o) => o.clone(),
        None => std::process::exit(emit_invalid("E-INPUT", "cert must be an object")),
    };

    // required_algs
    let required_algs: Vec<String> = match input.get("required_algs").and_then(|v| v.as_array()) {
        Some(arr) => arr.iter().filter_map(|v| v.as_str().map(String::from)).collect(),
        None => std::process::exit(emit_invalid("E-INPUT", "required_algs must be an array of strings")),
    };

    // signatures
    let signatures = match cert.get("signatures").and_then(|v| v.as_array()) {
        Some(arr) if !arr.is_empty() => arr.clone(),
        _ => std::process::exit(emit_invalid(
            "E_SIGNATURE_HYBRID_MISSING",
            "signatures array is empty",
        )),
    };

    // duplicate alg check
    let mut algs_seen: Vec<String> = Vec::with_capacity(signatures.len());
    for s in &signatures {
        if let Some(a) = s.get("alg").and_then(|v| v.as_str()) {
            algs_seen.push(a.to_string());
        }
    }
    {
        let mut sorted = algs_seen.clone();
        sorted.sort();
        sorted.dedup();
        if sorted.len() != algs_seen.len() {
            std::process::exit(emit_invalid(
                "E_SIGNATURE_DUPLICATE_ALG",
                &format!("algs: {:?}", algs_seen),
            ));
        }
    }

    // unknown alg check
    for alg in &algs_seen {
        if !ALLOWED_ALGS.contains(&alg.as_str()) {
            std::process::exit(emit_invalid(
                "E_SIGNATURE_UNKNOWN_ALG",
                &format!("alg: {:?}", alg),
            ));
        }
    }

    // downgrade check
    for req in &required_algs {
        if !algs_seen.contains(req) {
            std::process::exit(emit_invalid(
                "E_SIGNATURE_DOWNGRADE",
                &format!("required {:?} absent; present: {:?}", req, algs_seen),
            ));
        }
    }

    // TBS: build from cert without signatures
    // We must replicate Python's build_tbs exactly:
    //   DOMAIN_TAG (12 bytes) || JCS(cert_without_signatures)
    // JCS here uses the existing claim_root::canonical_bytes (stableStringify).
    use adie_primitives::jcs::canonical_bytes;

    let mut cert_wo: serde_json::Map<String, Value> = cert.clone();
    cert_wo.remove("signatures");
    cert_wo.remove("signature");
    let cert_wo_value = Value::Object(cert_wo);

    let canonical = match canonical_bytes(&cert_wo_value) {
        Ok(b) => b,
        Err(e) => std::process::exit(emit_invalid("E-INTERNAL", &format!("canonical: {}", e))),
    };

    const DOMAIN_TAG: &[u8] = b"ADIE-SIG-V2\x00";
    let mut tbs: Vec<u8> = Vec::with_capacity(DOMAIN_TAG.len() + canonical.len());
    tbs.extend_from_slice(DOMAIN_TAG);
    tbs.extend_from_slice(&canonical);

    // public_keys
    let public_keys = input.get("public_keys").and_then(|v| v.as_object()).cloned();

    // verify each required alg
    let mut checks: BTreeMap<String, String> = BTreeMap::new();
    let mut all_valid = true;

    for alg in &required_algs {
        // find signature
        let sig_obj = match signatures.iter().find(|s| s.get("alg").and_then(|v| v.as_str()) == Some(alg.as_str())) {
            Some(s) => s,
            None => {
                std::process::exit(emit_invalid("E_SIGNATURE_HYBRID_MISSING",
                    &format!("required {} not present in signatures", alg)));
            }
        };

        // decode base64
        let value_str = sig_obj.get("value").and_then(|v| v.as_str()).unwrap_or("");
        if !value_str.starts_with("base64:") {
            checks.insert(alg.clone(), "FAIL".to_string());
            all_valid = false;
            continue;
        }
        let b64 = &value_str[7..];
        let sig_bytes = match base64_decode(b64) {
            Some(b) => b,
            None => {
                checks.insert(alg.clone(), "FAIL".to_string());
                all_valid = false;
                continue;
            }
        };

        // key_id extraction from signature object
        let cert_key_id = sig_obj.get("key_id").and_then(|v| v.as_str()).unwrap_or("");

        let ok = match alg.as_str() {
            "RS256" => {
                let pk_pem = match public_keys.as_ref().and_then(|m| m.get("RS256")).and_then(|v| v.as_str()) {
                    Some(s) => s,
                    None => std::process::exit(emit_invalid("E_SIGNATURE_HYBRID_MISSING",
                        "RS256 required but pub key not provided")),
                };
                // key_id match first
                let expected_key_id = match rs256_key_id_from_pem(pk_pem.as_bytes()) {
                    Ok(k) => k,
                    Err(e) => std::process::exit(emit_invalid("E-INTERNAL", &format!("rs256 key_id: {}", e))),
                };
                if cert_key_id != expected_key_id {
                    let msg = format!("RS256 key_id mismatch: cert={:?} vs key={:?}",
                        cert_key_id, expected_key_id);
                    std::process::exit(emit_invalid("E_SIGNATURE_KEY_MISMATCH",
                        &take_chars(&msg, 120)));
                }
                match rsa_verify::verify_rs256_pkcs1v15(pk_pem.as_bytes(), &tbs, &sig_bytes) {
                    Ok(b) => b,
                    Err(_) => false,
                }
            }
            "ML-DSA-65" => {
                let pk_hex = match public_keys.as_ref().and_then(|m| m.get("ML-DSA-65")).and_then(|v| v.as_str()) {
                    Some(s) => s,
                    None => std::process::exit(emit_invalid("E_SIGNATURE_HYBRID_MISSING",
                        "ML-DSA-65 required but pub key not provided")),
                };
                let pk_raw = match hex::decode(pk_hex) {
                    Ok(b) => b,
                    Err(_) => std::process::exit(emit_invalid("E-INPUT", "ML-DSA-65 pk hex decode failed")),
                };
                // key_id match first
                let expected_key_id = match mldsa65_key_id_from_raw(&pk_raw) {
                    Ok(k) => k,
                    Err(e) => std::process::exit(emit_invalid("E-INTERNAL", &format!("mldsa key_id: {}", e))),
                };
                if cert_key_id != expected_key_id {
                    let msg = format!("ML-DSA-65 key_id mismatch: cert={:?} vs key={:?}",
                        cert_key_id, expected_key_id);
                    std::process::exit(emit_invalid("E_SIGNATURE_KEY_MISMATCH",
                        &take_chars(&msg, 120)));
                }
                match mldsa::verify_with_ctx(&pk_raw, &tbs, b"", &sig_bytes) {
                    Ok(b) => b,
                    Err(_) => false,
                }
            }
            _ => false,
        };

        checks.insert(alg.clone(), if ok { "PASS".to_string() } else { "FAIL".to_string() });
        if !ok {
            all_valid = false;
        }
    }

    if !all_valid {
        let msg = format!("checks: {:?}", checks);
        std::process::exit(emit_invalid("E_SIGNATURE_HYBRID_INVALID",
            &take_chars(&msg, 120)));
    }

    std::process::exit(emit_valid(&checks));
}

// Minimal base64 decode (standard alphabet, no padding errors ignored).
fn base64_decode(s: &str) -> Option<Vec<u8>> {
    fn val(c: u8) -> Option<u8> {
        match c {
            b'A'..=b'Z' => Some(c - b'A'),
            b'a'..=b'z' => Some(c - b'a' + 26),
            b'0'..=b'9' => Some(c - b'0' + 52),
            b'+' => Some(62),
            b'/' => Some(63),
            _ => None,
        }
    }
    let bytes: Vec<u8> = s.bytes().filter(|&b| b != b'=').collect();
    if bytes.len() % 4 == 1 { return None; }
    let mut out = Vec::with_capacity(bytes.len() * 3 / 4);
    let mut buf: u32 = 0;
    let mut bits = 0u32;
    for &b in &bytes {
        let v = val(b)? as u32;
        buf = (buf << 6) | v;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((buf >> bits) as u8);
        }
    }
    Some(out)
}

//! B+ envelope (WIRE-FORMAT-0.2-AMENDMENT-2 / DECISION-0.4).
//!
//! Model: integer-keyed deterministic CBOR top-level map; nested ADIE
//! objects carried as canonical JCS UTF-8 byte strings.
//!
//! NOT COSE. NOT COSE_Sign. NOT COSE_Sign1.

use serde_json::Value;

use crate::cbor::decoder::decode;
use crate::cbor::encoder::encode;
use crate::cbor::error::CborError;
use crate::cbor::value::AdieValue;
use crate::jcs::canonical_bytes;

const LBL_DCP_VERSION: u64 = 1;
const LBL_CLAIM_ID:    u64 = 2;
const LBL_ISSUER:      u64 = 3;
const LBL_SUBJECT:     u64 = 4;
const LBL_REQUEST:     u64 = 5;
const LBL_CONTEXT:     u64 = 6;
const LBL_POLICY:      u64 = 7;
const LBL_MODEL:       u64 = 8;
const LBL_DATA:        u64 = 9;
const LBL_RUNTIME:     u64 = 10;
const LBL_OUTPUT:      u64 = 11;
const LBL_BINDING:     u64 = 12;
const LBL_TEMPORAL:    u64 = 13;
const LBL_EVIDENCE:    u64 = 14;
const LBL_AUTHORING:   u64 = 15;
const LBL_PROOFS:      u64 = 16;
const LBL_CLAIM_ROOT:  u64 = 17;
const LBL_SIGNATURES:  u64 = 18;

const NESTED: [(&str, u64); 13] = [
    ("issuer",    LBL_ISSUER),
    ("subject",   LBL_SUBJECT),
    ("request",   LBL_REQUEST),
    ("context",   LBL_CONTEXT),
    ("policy",    LBL_POLICY),
    ("model",     LBL_MODEL),
    ("data",      LBL_DATA),
    ("runtime",   LBL_RUNTIME),
    ("output",    LBL_OUTPUT),
    ("binding",   LBL_BINDING),
    ("temporal",  LBL_TEMPORAL),
    ("evidence",  LBL_EVIDENCE),
    ("authoring", LBL_AUTHORING),
];

fn malformed(msg: impl Into<String>) -> CborError {
    CborError::Malformed { detail: msg.into() }
}

fn hex_decode(s: &str) -> Result<Vec<u8>, CborError> {
    if s.len() % 2 != 0 {
        return Err(malformed("envelope: odd hex length"));
    }
    let b = s.as_bytes();
    let mut out = Vec::with_capacity(b.len() / 2);
    for i in (0..b.len()).step_by(2) {
        let hi = (b[i] as char).to_digit(16)
            .ok_or_else(|| malformed("envelope: bad hex"))? as u8;
        let lo = (b[i+1] as char).to_digit(16)
            .ok_or_else(|| malformed("envelope: bad hex"))? as u8;
        out.push((hi << 4) | lo);
    }
    Ok(out)
}

fn hex_encode(b: &[u8]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}

fn base64_decode(s: &str) -> Result<Vec<u8>, CborError> {
    const A: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut rev = [255u8; 256];
    for (i, &c) in A.iter().enumerate() { rev[c as usize] = i as u8; }
    let s = s.trim_end_matches('=');
    let mut out = Vec::with_capacity(s.len() * 3 / 4);
    let mut buf: u32 = 0; let mut bits: u32 = 0;
    for &c in s.as_bytes() {
        let v = rev[c as usize];
        if v == 255 { return Err(malformed("envelope: bad base64 char")); }
        buf = (buf << 6) | v as u32;
        bits += 6;
        if bits >= 8 { bits -= 8; out.push(((buf >> bits) & 0xFF) as u8); }
    }
    Ok(out)
}

fn base64_encode(data: &[u8]) -> String {
    const A: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity((data.len() + 2) / 3 * 4);
    let mut i = 0;
    while i + 3 <= data.len() {
        let n = ((data[i] as u32) << 16) | ((data[i+1] as u32) << 8) | data[i+2] as u32;
        out.push(A[((n >> 18) & 63) as usize] as char);
        out.push(A[((n >> 12) & 63) as usize] as char);
        out.push(A[((n >> 6) & 63) as usize] as char);
        out.push(A[(n & 63) as usize] as char);
        i += 3;
    }
    match data.len() - i {
        1 => {
            let n = (data[i] as u32) << 16;
            out.push(A[((n >> 18) & 63) as usize] as char);
            out.push(A[((n >> 12) & 63) as usize] as char);
            out.push('='); out.push('=');
        }
        2 => {
            let n = ((data[i] as u32) << 16) | ((data[i+1] as u32) << 8);
            out.push(A[((n >> 18) & 63) as usize] as char);
            out.push(A[((n >> 12) & 63) as usize] as char);
            out.push(A[((n >> 6) & 63) as usize] as char);
            out.push('=');
        }
        _ => {}
    }
    out
}

pub fn build_envelope(cert_json: &str) -> Result<Vec<u8>, CborError> {
    let cert: Value = serde_json::from_str(cert_json)
        .map_err(|e| malformed(format!("envelope: cert JSON: {}", e)))?;
    let obj = cert.as_object()
        .ok_or_else(|| malformed("envelope: cert must be JSON object"))?;

    let dcp_version = obj.get("dcp_version").and_then(|v| v.as_str())
        .ok_or_else(|| malformed("envelope: missing dcp_version"))?
        .to_string();
    let claim_id = obj.get("claim_id").and_then(|v| v.as_str())
        .ok_or_else(|| malformed("envelope: missing claim_id"))?
        .to_string();

    let mut entries: Vec<(u64, AdieValue)> = Vec::with_capacity(18);
    entries.push((LBL_DCP_VERSION, AdieValue::Text(dcp_version)));
    entries.push((LBL_CLAIM_ID, AdieValue::Text(claim_id)));

    for (name, lbl) in NESTED {
        let field = obj.get(name)
            .ok_or_else(|| malformed(format!("envelope: missing {}", name)))?;
        if !field.is_object() {
            return Err(malformed(format!("envelope: {} must be object", name)));
        }
        let jcs = canonical_bytes(field)
            .map_err(|e| malformed(format!("envelope: {} JCS: {}", name, e)))?;
        entries.push((lbl, AdieValue::Bytes(jcs)));
    }

    // proofs (16): reserved — only empty array supported
    let proofs = obj.get("proofs")
        .and_then(|v| v.as_array())
        .ok_or_else(|| malformed("envelope: missing proofs array"))?;
    if !proofs.is_empty() {
        return Err(malformed("envelope: non-empty proofs reserved"));
    }
    entries.push((LBL_PROOFS, AdieValue::Array(vec![])));

    // claim_root (17): 32 raw bytes
    let cr_str = obj.get("claim_root").and_then(|v| v.as_str())
        .ok_or_else(|| malformed("envelope: missing claim_root"))?;
    let cr_hex = cr_str.strip_prefix("sha256:")
        .ok_or_else(|| malformed("envelope: claim_root must start sha256:"))?;
    let cr_bytes = hex_decode(cr_hex)?;
    if cr_bytes.len() != 32 {
        return Err(malformed(format!("envelope: claim_root must be 32 bytes, got {}", cr_bytes.len())));
    }
    entries.push((LBL_CLAIM_ROOT, AdieValue::Bytes(cr_bytes)));

    // signatures (18): array of {1:alg, 2:kid, 3:raw_sig}
    let sigs = obj.get("signatures").and_then(|v| v.as_array())
        .ok_or_else(|| malformed("envelope: missing signatures"))?;
    let mut sig_objs: Vec<AdieValue> = Vec::with_capacity(sigs.len());
    for s in sigs {
        let so = s.as_object()
            .ok_or_else(|| malformed("envelope: signature must be object"))?;
        let alg = so.get("alg").and_then(|v| v.as_str()).ok_or_else(|| malformed("envelope: sig.alg"))?;
        let kid = so.get("key_id").and_then(|v| v.as_str()).ok_or_else(|| malformed("envelope: sig.key_id"))?;
        let val = so.get("value").and_then(|v| v.as_str()).ok_or_else(|| malformed("envelope: sig.value"))?;
        let raw = val.strip_prefix("base64:").ok_or_else(|| malformed("envelope: sig.value must start base64:"))?;
        let raw_bytes = base64_decode(raw)?;
        let mut sm: Vec<(u64, AdieValue)> = Vec::with_capacity(3);
        sm.push((1, AdieValue::Text(alg.to_string())));
        sm.push((2, AdieValue::Text(kid.to_string())));
        sm.push((3, AdieValue::Bytes(raw_bytes)));
        sig_objs.push(AdieValue::Map(sm));
    }
    entries.push((LBL_SIGNATURES, AdieValue::Array(sig_objs)));

    encode(&AdieValue::Map(entries))
}

pub fn parse_envelope(bytes: &[u8]) -> Result<String, CborError> {
    let val = decode(bytes)?;
    let entries = match val {
        AdieValue::Map(m) => m,
        _ => return Err(malformed("envelope: top-level must be map")),
    };

    let mut cert = serde_json::Map::new();
    let mut sigs_opt: Option<Vec<Value>> = None;
    let mut seen: [bool; 19] = [false; 19];

    for (label, av) in entries {
        if label > 18 {
            return Err(malformed(format!("envelope: unknown label {}", label)));
        }
        if seen[label as usize] {
            return Err(malformed(format!("envelope: duplicate label {}", label)));
        }
        seen[label as usize] = true;

        match label {
            LBL_DCP_VERSION => {
                let s = match av { AdieValue::Text(t) => t, _ => return Err(malformed("envelope: dcp_version must be text")) };
                cert.insert("dcp_version".into(), Value::String(s));
            }
            LBL_CLAIM_ID => {
                let s = match av { AdieValue::Text(t) => t, _ => return Err(malformed("envelope: claim_id must be text")) };
                cert.insert("claim_id".into(), Value::String(s));
            }
            3..=15 => {
                let name = NESTED.iter().find(|(_, l)| *l == label).map(|(n, _)| *n).unwrap();
                let jcs = match av { AdieValue::Bytes(b) => b, _ => return Err(malformed(format!("envelope: {} must be bstr", name))) };
                // UTF-8 validation
                let _ = std::str::from_utf8(&jcs).map_err(|_| malformed(format!("envelope: {} not UTF-8", name)))?;
                // JSON parse
                let v: Value = serde_json::from_slice(&jcs)
                    .map_err(|e| malformed(format!("envelope: {} not JSON: {}", name, e)))?;
                if !v.is_object() {
                    return Err(malformed(format!("envelope: {} must be JSON object", name)));
                }
                // JCS canonical re-serialize check
                let re = canonical_bytes(&v)
                    .map_err(|e| malformed(format!("envelope: {} JCS re: {}", name, e)))?;
                if re != jcs {
                    return Err(malformed(format!("envelope: {} JCS non-canonical", name)));
                }
                cert.insert(name.into(), v);
            }
            LBL_PROOFS => {
                match av {
                    AdieValue::Array(a) if a.is_empty() => { cert.insert("proofs".into(), Value::Array(vec![])); }
                    _ => return Err(malformed("envelope: non-empty proofs reserved")),
                }
            }
            LBL_CLAIM_ROOT => {
                let raw = match av { AdieValue::Bytes(b) => b, _ => return Err(malformed("envelope: claim_root must be bstr")) };
                if raw.len() != 32 { return Err(malformed("envelope: claim_root must be 32 bytes")); }
                cert.insert("claim_root".into(), Value::String(format!("sha256:{}", hex_encode(&raw))));
            }
            LBL_SIGNATURES => {
                let arr = match av { AdieValue::Array(a) => a, _ => return Err(malformed("envelope: signatures must be array")) };
                let mut out = Vec::with_capacity(arr.len());
                for s in arr {
                    let m = match s { AdieValue::Map(m) => m, _ => return Err(malformed("envelope: signature must be map")) };
                    let mut alg = String::new(); let mut kid = String::new(); let mut raw = Vec::new();
                    for (l, v) in m {
                        match l {
                            1 => alg = match v { AdieValue::Text(t) => t, _ => return Err(malformed("sig.alg must be text")) },
                            2 => kid = match v { AdieValue::Text(t) => t, _ => return Err(malformed("sig.key_id must be text")) },
                            3 => raw = match v { AdieValue::Bytes(b) => b, _ => return Err(malformed("sig.value must be bstr")) },
                            _ => return Err(malformed(format!("sig: unknown inner label {}", l))),
                        }
                    }
                    out.push(serde_json::json!({
                        "alg": alg, "key_id": kid,
                        "value": format!("base64:{}", base64_encode(&raw)),
                    }));
                }
                sigs_opt = Some(out);
            }
            _ => unreachable!(),
        }
    }

    // required-field presence
    for req in ["dcp_version", "claim_id", "issuer", "subject", "request", "context",
                "policy", "model", "data", "runtime", "output", "binding",
                "temporal", "evidence", "authoring", "proofs", "claim_root"] {
        if !cert.contains_key(req) {
            return Err(malformed(format!("envelope: missing required field {}", req)));
        }
    }
    cert.insert("signatures".into(), Value::Array(sigs_opt.ok_or_else(|| malformed("envelope: missing signatures"))?));

    Ok(Value::Object(cert).to_string())
}

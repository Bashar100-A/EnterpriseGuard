//! ADIE-PILOT v0.1 — Rust semantic verifier (Phase 1.12-lite).
//! Verifies every layer except signature. See spec/RUST-VERIFIER-0.1.md.
use std::collections::BTreeMap;
use serde_json::{json, Value};
use crate::claim_root::claim_root_hex;
use crate::jcs::canonical_bytes;
use crate::h_a::h_a;
use crate::acl::canonical_bytes_of;

const REQUIRED_FIELDS: &[&str] = &[
    "dcp_version","claim_id","issuer","subject","binding",
    "request","context","policy","model","data","runtime",
    "output","temporal","evidence","authoring",
    "proofs","claim_root","signature",
];

const FIELD_NAMES_13: &[&str] = &[
    "issuer","subject","request","context","policy","model","data",
    "runtime","output","binding","temporal","evidence","authoring",
];

const REQUIRED_AUTHORING_KEYS: &[&str] = &[
    "acl_version","canonical_ast_digest","compiler_digest",
    "meta_manifest_digest","parameter_digest","template_digest",
];

const ACL_VERSION: &str = "0.1";

#[derive(Debug)]
pub struct VerifyError {
    pub code: String,
    pub message: String,  // final message, ready to emit
}

fn take_chars(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

fn fail_dcp<T>(code: &str, msg: &str) -> Result<T, VerifyError> {
    let full = format!("{}: {}", code, msg);
    let sliced = take_chars(&full, 120);
    Err(VerifyError { code: code.into(), message: sliced })
}

fn fail_binding<T>(code: &str, binding_msg: &str) -> Result<T, VerifyError> {
    let inner = format!("{}: {}", code, binding_msg);
    let inner_sliced = take_chars(&inner, 80);
    fail_dcp(code, &inner_sliced)
}

fn fail_direct<T>(code: &str, msg: &str) -> Result<T, VerifyError> {
    Err(VerifyError { code: code.into(), message: msg.into() })
}

fn py_repr(v: &Value) -> String {
    match v {
        Value::Null => "None".to_string(),
        Value::Bool(true) => "True".to_string(),
        Value::Bool(false) => "False".to_string(),
        Value::Number(n) => n.to_string(),
        Value::String(s) => format!("'{}'", s),
        _ => v.to_string(),
    }
}

fn is_sha256(s: &str) -> bool {
    s.len() == 71 && s.starts_with("sha256:")
        && s[7..].bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

fn take_n(s: &str, n: usize) -> &str {
    let mut end = 0;
    let mut count = 0;
    for (i, c) in s.char_indices() {
        if count >= n { break; }
        end = i + c.len_utf8();
        count += 1;
    }
    &s[..end]
}

fn request_hash(request: &Value) -> Result<String, VerifyError> {
    let canon = canonical_bytes(request).map_err(|e| VerifyError {
        code: "E-INTERNAL".into(), message: e })?;
    Ok(format!("sha256:{}", crate::hex::encode(&h_a("request", &canon))))
}

pub fn verify_semantic(
    cert: &Value,
    expected_audience: Option<&str>,
) -> Result<BTreeMap<String, String>, VerifyError> {
    // 1. Top-level object
    let obj = cert.as_object()
        .ok_or_else(|| VerifyError {
            code: "E_SCHEMA".into(),
            message: "E_SCHEMA: top-level must be object".into(),
        })?;

    // 2. Required fields
    for f in REQUIRED_FIELDS {
        if !obj.contains_key(*f) {
            return fail_dcp("E_SCHEMA", &format!("missing {}", f));
        }
    }

    // 3. dcp_version
    let dcv = obj.get("dcp_version").unwrap();
    if dcv.as_str() != Some("2.0") {
        return fail_dcp("E_VERSION", &format!(
            "dcp_version must be 2.0, got {}", py_repr(dcv)));
    }

    // 4. ClaimRoot
    let mut fields_map = serde_json::Map::new();
    for name in FIELD_NAMES_13 {
        let v = obj.get(*name).cloned().unwrap_or(Value::Null);
        fields_map.insert(name.to_string(), v);
    }
    let fields = Value::Object(fields_map);
    let recomputed = claim_root_hex(&fields).map_err(|e| VerifyError {
        code: "E-INTERNAL".into(), message: e })?;
    let declared = obj.get("claim_root").and_then(|v| v.as_str()).unwrap_or("");
    if declared != recomputed {
        return fail_dcp("E_CLAIM_ROOT_MISMATCH", &format!(
            "declared {}, recomputed {}",
            take_n(declared, 24), take_n(&recomputed, 24)));
    }

    // 5. Binding
    let binding = obj.get("binding").and_then(|v| v.as_object())
        .ok_or_else(|| VerifyError {
            code: "E-BINDING-MISSING-FIELD".into(),
            message: "E-BINDING-MISSING-FIELD: binding".into() })?;

    for f in ["audience","purpose","resource","request_hash","nonce","certificate_id"] {
        if !binding.contains_key(f) {
            return fail_binding("E-BINDING-MISSING-FIELD", f);
        }
    }

    let request = obj.get("request").unwrap_or(&Value::Null);
    let re_req_h = request_hash(request)?;
    let declared_req_h = binding.get("request_hash")
        .and_then(|v| v.as_str()).unwrap_or("");
    if declared_req_h != re_req_h {
        return fail_binding("E-BINDING-REQUEST-HASH", &format!(
            "declared {}, recomputed {}",
            take_n(declared_req_h, 20), take_n(&re_req_h, 20)));
    }

    if let Some(exp) = expected_audience {
        let got = binding.get("audience").and_then(|v| v.as_str()).unwrap_or("");
        if got != exp {
            return fail_binding("E-BINDING-AUDIENCE-MISMATCH", &format!(
                "expected {}, got {}", exp, got));
        }
    }

    // 6. Authoring closure (verify_cli-level checks — direct messages)
    let auth = obj.get("authoring").and_then(|v| v.as_object())
        .ok_or_else(|| VerifyError {
            code: "E-META-20".into(),
            message: "authoring missing".into() })?;
    if auth.len() != REQUIRED_AUTHORING_KEYS.len() {
        return fail_direct("E-META-20", "authoring keys mismatch");
    }
    for k in REQUIRED_AUTHORING_KEYS {
        if !auth.contains_key(*k) {
            return fail_direct("E-META-20", "authoring keys mismatch");
        }
    }
    for k in ["template_digest","parameter_digest","compiler_digest",
              "canonical_ast_digest","meta_manifest_digest"] {
        let v = auth.get(k).and_then(|x| x.as_str()).unwrap_or("");
        if !is_sha256(v) {
            return fail_direct("E-META-20", &format!("{} malformed", k));
        }
    }
    let auth_acl = auth.get("acl_version").and_then(|v| v.as_str()).unwrap_or("");
    if auth_acl != ACL_VERSION {
        return fail_direct("E-META-14",
            &format!("authoring.acl_version != {}", ACL_VERSION));
    }

    // 7. AST canonicalization
    let policy = obj.get("policy").and_then(|v| v.as_object())
        .ok_or_else(|| VerifyError {
            code: "E-META-18".into(),
            message: "policy missing".into() })?;
    let ast = policy.get("expression")
        .ok_or_else(|| VerifyError {
            code: "E-META-18".into(),
            message: "policy.expression missing".into() })?;
    if !ast.is_object() {
        return fail_direct("E-META-18", "policy.expression missing");
    }
    let canonical_bytes_val = canonical_bytes_of(ast)
        .map_err(|e| VerifyError {
            code: e.code.clone(),
            message: take_chars(&format!("{}: {}", e.code, e.message), 120) })?;
    let expected_ast = format!("sha256:{}", crate::hex::encode(&h_a("ast", &canonical_bytes_val)));
    let declared_ast = auth.get("canonical_ast_digest")
        .and_then(|v| v.as_str()).unwrap_or("");
    if expected_ast != declared_ast {
        return fail_direct("E-META-20", "canonical_ast_digest mismatch");
    }

    // 8. Success
    let mut checks = BTreeMap::new();
    checks.insert("acl_version".to_string(), "PASS".to_string());
    checks.insert("ast_canonicalization".to_string(), "PASS".to_string());
    checks.insert("authoring_closure".to_string(), "PASS".to_string());
    checks.insert("binding".to_string(), "PASS".to_string());
    checks.insert("claim_root".to_string(), "PASS".to_string());
    checks.insert("dcp20".to_string(), "PASS".to_string());
    checks.insert("signature".to_string(), "SKIPPED".to_string());
    Ok(checks)
}

pub fn emit_valid_json(checks: &BTreeMap<String, String>) -> String {
    let v = json!({ "checks": checks, "status": "VALID" });
    String::from_utf8(canonical_bytes(&v).unwrap()).unwrap()
}

pub fn emit_invalid_json(err: &VerifyError) -> String {
    let v = json!({
        "code": err.code,
        "message": err.message,
        "status": "INVALID"
    });
    String::from_utf8(canonical_bytes(&v).unwrap()).unwrap()
}

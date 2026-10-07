//! adie-wasm — WASM delivery wrapper for adie-primitives (3A.4B).
//!
//! Trust boundary:
//!   adie-primitives = reference implementation (authority)
//!   this crate      = thin delivery wrapper (no new semantics)
//!
//! ABI contract (WASM ABI / serialization boundary, NOT DCP 2.1 schema):
//!   - Values cross the boundary as UTF-8 JSON strings.
//!   - u64/i64 fields (v in uint/int, AND map keys) are STRINGS.
//!   - Never routed through JavaScript Number. See DEFECT-029-WASM.
//!   - CBOR bytes cross as Uint8Array (Vec<u8> / &[u8]).

use wasm_bindgen::prelude::*;
use serde_json::{json, Value};

use adie_primitives::cbor::decoder::decode as rust_decode;
use adie_primitives::cbor::encoder::encode as rust_encode;
use adie_primitives::cbor::error::CborError;
use adie_primitives::cbor::value::AdieValue;

// ─── AdieValue → JSON (u64/i64 as strings) ────────────────────────

fn value_to_json(v: &AdieValue) -> Value {
    match v {
        AdieValue::UInt(n)  => json!({"t":"uint", "v": n.to_string()}),
        AdieValue::Int(n)   => json!({"t":"int",  "v": n.to_string()}),
        AdieValue::Bytes(b) => json!({"t":"bytes","v": hex_encode(b)}),
        AdieValue::Text(s)  => json!({"t":"text", "v": s}),
        AdieValue::Bool(b)  => json!({"t":"bool", "v": b}),
        AdieValue::Null     => json!({"t":"null"}),
        AdieValue::Array(items) => {
            let arr: Vec<Value> = items.iter().map(value_to_json).collect();
            json!({"t":"array","v": arr})
        }
        AdieValue::Map(entries) => {
            let pairs: Vec<Value> = entries.iter()
                .map(|(k, v)| json!([k.to_string(), value_to_json(v)]))
                .collect();
            json!({"t":"map","v": pairs})
        }
    }
}

// ─── JSON → AdieValue (accepts string for u64/i64; tolerant Number legacy) ─

fn json_to_value(v: &Value) -> Result<AdieValue, String> {
    let obj = v.as_object().ok_or("value must be object")?;
    let t = obj.get("t").and_then(|x| x.as_str()).ok_or("missing t")?;
    match t {
        "uint" => Ok(AdieValue::UInt(read_u64(obj.get("v"))?)),
        "int"  => Ok(AdieValue::Int(read_i64(obj.get("v"))?)),
        "bytes" => {
            let h = obj.get("v").and_then(|x| x.as_str()).ok_or("bytes v")?;
            Ok(AdieValue::Bytes(hex_decode(h).map_err(|e| format!("hex: {}", e))?))
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
            for item in arr { out.push(json_to_value(item)?); }
            Ok(AdieValue::Array(out))
        }
        "map" => {
            let arr = obj.get("v").and_then(|x| x.as_array()).ok_or("map v")?;
            let mut out = Vec::with_capacity(arr.len());
            for pair in arr {
                let p = pair.as_array().ok_or("pair not array")?;
                if p.len() != 2 { return Err("pair must be [k,v]".into()); }
                let k = read_u64(Some(&p[0]))?;
                let v = json_to_value(&p[1])?;
                out.push((k, v));
            }
            Ok(AdieValue::Map(out))
        }
        other => Err(format!("unknown type tag {:?}", other)),
    }
}

// read_u64: accepts JSON string (primary, DEFECT-029-WASM) or JSON
// number (legacy tolerance for cross-endpoint reuse).
fn read_u64(v: Option<&Value>) -> Result<u64, String> {
    let v = v.ok_or("missing v")?;
    if let Some(s) = v.as_str() {
        return s.parse::<u64>().map_err(|_| format!("E_ABI: u64 out of range: {}", s));
    }
    if let Some(n) = v.as_u64() { return Ok(n); }
    Err(format!("E_ABI: v must be decimal string, got {:?}", v))
}

fn read_i64(v: Option<&Value>) -> Result<i64, String> {
    let v = v.ok_or("missing v")?;
    if let Some(s) = v.as_str() {
        return s.parse::<i64>().map_err(|_| format!("E_ABI: i64 out of range: {}", s));
    }
    if let Some(n) = v.as_i64() { return Ok(n); }
    Err(format!("E_ABI: v must be decimal string, got {:?}", v))
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
        let lo = (bytes[i+1] as char).to_digit(16).ok_or("bad hex")? as u8;
        out.push((hi << 4) | lo);
    }
    Ok(out)
}

// ─── Error mapping ────────────────────────────────────────────────

fn cbor_err_to_js(e: CborError) -> JsValue {
    JsValue::from_str(e.code())
}

// ─── Public WASM API ──────────────────────────────────────────────

/// Encode an AdieValue (JSON string) to canonical DCP 2.1 CBOR.
/// Returns Uint8Array. On error throws with an E_WIRE_* or E_ABI/E_JSON code.
#[wasm_bindgen]
pub fn encode(value_json: &str) -> Result<Vec<u8>, JsValue> {
    let json: Value = serde_json::from_str(value_json)
        .map_err(|e| JsValue::from_str(&format!("E_JSON: {}", e)))?;
    let av = json_to_value(&json).map_err(|e| JsValue::from_str(&e))?;
    rust_encode(&av).map_err(cbor_err_to_js)
}

/// Decode canonical DCP 2.1 CBOR to an AdieValue (JSON string).
/// u64/i64 fields (values AND map keys) are returned as strings.
/// On error throws with an E_WIRE_* code.
#[wasm_bindgen]
pub fn decode(bytes: &[u8]) -> Result<String, JsValue> {
    let av = rust_decode(bytes).map_err(cbor_err_to_js)?;
    Ok(value_to_json(&av).to_string())
}

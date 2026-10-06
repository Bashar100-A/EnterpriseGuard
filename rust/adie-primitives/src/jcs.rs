//! JCS subset — canonical JSON serialization (RFC 8785 subset).
//! Matches Python json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).
use serde_json::Value;

/// Escape a string matching Python json.dumps with ensure_ascii=False.
/// Python escapes: \" \\ \n \r \t \b \f and \uXXXX for other ctrl chars.
/// Non-ASCII is kept as UTF-8 (no escaping).
fn write_json_string(s: &str, out: &mut Vec<u8>) {
    out.push(b'"');
    for c in s.chars() {
        match c {
            '"'  => out.extend_from_slice(b"\\\""),
            '\\' => out.extend_from_slice(b"\\\\"),
            '\n' => out.extend_from_slice(b"\\n"),
            '\r' => out.extend_from_slice(b"\\r"),
            '\t' => out.extend_from_slice(b"\\t"),
            '\u{08}' => out.extend_from_slice(b"\\b"),
            '\u{0C}' => out.extend_from_slice(b"\\f"),
            c if (c as u32) < 0x20 => {
                out.extend_from_slice(format!("\\u{:04x}", c as u32).as_bytes());
            }
            c => {
                let mut buf = [0u8; 4];
                out.extend_from_slice(c.encode_utf8(&mut buf).as_bytes());
            }
        }
    }
    out.push(b'"');
}

fn write_value(v: &Value, out: &mut Vec<u8>) -> Result<(), String> {
    match v {
        Value::Null => out.extend_from_slice(b"null"),
        Value::Bool(true) => out.extend_from_slice(b"true"),
        Value::Bool(false) => out.extend_from_slice(b"false"),
        Value::Number(n) => {
            // Reject non-integer numbers (matches our I-JSON subset).
            if !(n.is_i64() || n.is_u64()) {
                return Err(format!("non-integer number not allowed: {}", n));
            }
            out.extend_from_slice(n.to_string().as_bytes());
        }
        Value::String(s) => write_json_string(s, out),
        Value::Array(arr) => {
            out.push(b'[');
            for (i, item) in arr.iter().enumerate() {
                if i > 0 { out.push(b','); }
                write_value(item, out)?;
            }
            out.push(b']');
        }
        Value::Object(map) => {
            out.push(b'{');
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            for (i, k) in keys.iter().enumerate() {
                if i > 0 { out.push(b','); }
                write_json_string(k, out);
                out.push(b':');
                write_value(&map[*k], out)?;
            }
            out.push(b'}');
        }
    }
    Ok(())
}

pub fn canonical_bytes(v: &Value) -> Result<Vec<u8>, String> {
    let mut out = Vec::new();
    write_value(v, &mut out)?;
    Ok(out)
}

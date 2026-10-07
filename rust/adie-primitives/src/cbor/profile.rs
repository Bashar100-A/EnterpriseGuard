//! ADIE CBOR profile validation (Phase 3, Gate 1, 3A.2).
//!
//! Normative source: spec/WIRE-FORMAT-0.2.md §5, §7, §8, §9.
//!
//! This module is the **authority** that decides what CBOR value is
//! admissible as a DCP 2.1 payload. The encoder and decoder both go
//! through `validate()`; neither is itself an authority.

use ciborium::value::{Integer, Value};

use crate::cbor::error::CborError;
use crate::cbor::value::{canonicalize_map, AdieValue};

/// Maximum nesting depth (mirrors META-CONTRACT-0.1 / ACL-0.1 limits).
pub const MAX_DEPTH: usize = 32;

/// Validate a ciborium `Value` against the ADIE DCP 2.1 profile.
///
/// On success returns an `AdieValue` with maps canonicalized (sorted,
/// duplicate-free). On failure returns a specific `CborError`.
///
/// This function does NOT see raw bytes; it does not detect
/// indefinite-length encodings (which ciborium collapses). Those are
/// handled by the raw-byte pre-check in the decoder.
pub fn validate(value: &Value) -> Result<AdieValue, CborError> {
    validate_depth(value, 0)
}

fn validate_depth(value: &Value, depth: usize) -> Result<AdieValue, CborError> {
    if depth > MAX_DEPTH {
        return Err(CborError::Malformed {
            detail: format!("max nesting depth {} exceeded", MAX_DEPTH),
        });
    }
    match value {
        Value::Integer(i) => integer_to_adie(i),
        Value::Bytes(b) => Ok(AdieValue::Bytes(b.clone())),
        Value::Text(t) => Ok(AdieValue::Text(t.clone())),
        Value::Bool(b) => Ok(AdieValue::Bool(*b)),
        Value::Null => Ok(AdieValue::Null),
        Value::Array(arr) => {
            let mut out = Vec::with_capacity(arr.len());
            for v in arr {
                out.push(validate_depth(v, depth + 1)?);
            }
            Ok(AdieValue::Array(out))
        }
        Value::Map(pairs) => {
            let mut entries = Vec::with_capacity(pairs.len());
            for (k, v) in pairs {
                let key = match k {
                    Value::Integer(i) => integer_to_u64(i)?,
                    _ => {
                        return Err(CborError::TypeMismatch {
                            field: "map key",
                            expected: "unsigned integer",
                        })
                    }
                };
                let val = validate_depth(v, depth + 1)?;
                entries.push((key, val));
            }
            let sorted = canonicalize_map(entries)?;
            Ok(AdieValue::Map(sorted))
        }
        Value::Float(_) => Err(CborError::Float),
        Value::Tag(tag, _) => Err(CborError::Tag { tag: *tag }),
        // ciborium::Value is #[non_exhaustive]; reject anything we
        // do not recognise rather than silently accepting it.
        _ => Err(CborError::Malformed {
            detail: "unrecognised ciborium::Value variant (non_exhaustive)".into(),
        }),
    }
}

fn integer_to_adie(i: &Integer) -> Result<AdieValue, CborError> {
    // Try unsigned first.
    if let Ok(n) = u64::try_from(*i) {
        return Ok(AdieValue::UInt(n));
    }
    // Try signed.
    if let Ok(n) = i64::try_from(*i) {
        return Ok(AdieValue::Int(n));
    }
    // Out of both ranges — should be unreachable given ciborium's
    // representation, but reject defensively.
    Err(CborError::NonCanonicalInt)
}

fn integer_to_u64(i: &Integer) -> Result<u64, CborError> {
    u64::try_from(*i).map_err(|_| CborError::TypeMismatch {
        field: "map key",
        expected: "unsigned integer in u64 range",
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use ciborium::value::Integer;

    fn vint(n: i64) -> Value { Value::Integer(Integer::from(n)) }
    fn vuint(n: u64) -> Value { Value::Integer(Integer::from(n)) }
    fn vtext(s: &str) -> Value { Value::Text(s.into()) }
    fn vbytes(b: &[u8]) -> Value { Value::Bytes(b.into()) }

    // ── Primitives accepted ──
    #[test]
    fn accepts_null() {
        assert_eq!(validate(&Value::Null).unwrap(), AdieValue::Null);
    }

    #[test]
    fn accepts_bool() {
        assert_eq!(validate(&Value::Bool(true)).unwrap(), AdieValue::Bool(true));
        assert_eq!(validate(&Value::Bool(false)).unwrap(), AdieValue::Bool(false));
    }

    #[test]
    fn accepts_text() {
        assert_eq!(validate(&vtext("hello")).unwrap(),
                   AdieValue::Text("hello".into()));
    }

    #[test]
    fn accepts_bytes() {
        assert_eq!(validate(&vbytes(&[1, 2, 3])).unwrap(),
                   AdieValue::Bytes(vec![1, 2, 3]));
    }

    #[test]
    fn accepts_positive_int_as_uint() {
        assert_eq!(validate(&vuint(42)).unwrap(), AdieValue::UInt(42));
    }

    #[test]
    fn accepts_negative_int() {
        assert_eq!(validate(&vint(-1)).unwrap(), AdieValue::Int(-1));
    }

    // ── Floats rejected ──
    #[test]
    fn rejects_float() {
        assert!(matches!(validate(&Value::Float(1.0)),
                         Err(CborError::Float)));
    }

    // ── Tags rejected ──
    #[test]
    fn rejects_tag_0() {
        let v = Value::Tag(0, Box::new(vtext("date")));
        assert!(matches!(validate(&v), Err(CborError::Tag { tag: 0 })));
    }

    #[test]
    fn rejects_tag_42() {
        let v = Value::Tag(42, Box::new(Value::Null));
        assert!(matches!(validate(&v), Err(CborError::Tag { tag: 42 })));
    }

    // ── Arrays ──
    #[test]
    fn accepts_empty_array() {
        assert_eq!(validate(&Value::Array(vec![])).unwrap(),
                   AdieValue::Array(vec![]));
    }

    #[test]
    fn accepts_array_of_primitives() {
        let v = Value::Array(vec![vtext("a"), vuint(1), Value::Bool(true)]);
        let out = validate(&v).unwrap();
        assert_eq!(out, AdieValue::Array(vec![
            AdieValue::Text("a".into()),
            AdieValue::UInt(1),
            AdieValue::Bool(true),
        ]));
    }

    #[test]
    fn rejects_array_with_float() {
        let v = Value::Array(vec![vtext("a"), Value::Float(1.5)]);
        assert!(matches!(validate(&v), Err(CborError::Float)));
    }

    // ── Maps ──
    #[test]
    fn accepts_empty_map() {
        assert_eq!(validate(&Value::Map(vec![])).unwrap(),
                   AdieValue::Map(vec![]));
    }

    #[test]
    fn accepts_integer_keyed_map() {
        let v = Value::Map(vec![
            (vuint(2), vtext("b")),
            (vuint(1), vtext("a")),
        ]);
        let out = validate(&v).unwrap();
        // canonicalized: 1 before 2
        if let AdieValue::Map(entries) = out {
            assert_eq!(entries.len(), 2);
            assert_eq!(entries[0].0, 1);
            assert_eq!(entries[1].0, 2);
        } else {
            panic!("expected map");
        }
    }

    #[test]
    fn rejects_text_map_key() {
        let v = Value::Map(vec![(vtext("k"), vuint(1))]);
        assert!(matches!(validate(&v), Err(CborError::TypeMismatch { .. })));
    }

    #[test]
    fn rejects_bytes_map_key() {
        let v = Value::Map(vec![(vbytes(&[1, 2]), vuint(1))]);
        assert!(matches!(validate(&v), Err(CborError::TypeMismatch { .. })));
    }

    #[test]
    fn rejects_array_map_key() {
        let v = Value::Map(vec![(Value::Array(vec![]), vuint(1))]);
        assert!(matches!(validate(&v), Err(CborError::TypeMismatch { .. })));
    }

    #[test]
    fn rejects_duplicate_keys_in_map() {
        let v = Value::Map(vec![
            (vuint(1), vtext("a")),
            (vuint(1), vtext("b")),
        ]);
        assert!(matches!(validate(&v), Err(CborError::DuplicateKey)));
    }

    #[test]
    fn rejects_map_with_negative_key() {
        let v = Value::Map(vec![(vint(-1), vtext("x"))]);
        // negative keys are not unsigned-int, so rejected as TypeMismatch
        assert!(matches!(validate(&v), Err(CborError::TypeMismatch { .. })));
    }

    // ── Depth limit ──
    #[test]
    fn accepts_depth_32() {
        let mut v = Value::Null;
        for _ in 0..32 {
            v = Value::Array(vec![v]);
        }
        assert!(validate(&v).is_ok());
    }

    #[test]
    fn rejects_depth_33() {
        let mut v = Value::Null;
        for _ in 0..33 {
            v = Value::Array(vec![v]);
        }
        assert!(matches!(validate(&v), Err(CborError::Malformed { .. })));
    }

    // ── Composite ──
    #[test]
    fn accepts_nested_structure() {
        let v = Value::Map(vec![
            (vuint(1), vtext("version")),
            (vuint(2), Value::Array(vec![vuint(1), vuint(2)])),
            (vuint(3), Value::Map(vec![(vuint(10), Value::Bool(false))])),
        ]);
        let out = validate(&v).unwrap();
        if let AdieValue::Map(entries) = out {
            assert_eq!(entries.len(), 3);
            assert_eq!(entries[0].0, 1);
            assert_eq!(entries[1].0, 2);
            assert_eq!(entries[2].0, 3);
        } else {
            panic!();
        }
    }
}

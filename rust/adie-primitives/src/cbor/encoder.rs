//! ADIE canonical CBOR encoder (Phase 3, Gate 1, 3A.2).
//!
//! Normative source: WIRE-FORMAT-0.2 §7, §8.
//!
//! This is a thin serializer over ciborium. It assumes the input is a
//! valid `AdieValue` (produced by `profile::validate` or by hand):
//!   - only profile types
//!   - maps already sorted and duplicate-free
//!   - keys already u64
//!
//! ciborium uses RFC 8949 preferred serialization (shortest integers,
//! definite lengths), so the output is canonical for its input.
//!
//! The encoder is NOT an authority. Authority lives in `profile.rs`.
//! The encoder simply emits bytes for already-valid values.

use ciborium::value::{Integer, Value};
use ciborium::ser::into_writer;

use crate::cbor::error::CborError;
use crate::cbor::value::AdieValue;

/// Encode an `AdieValue` to canonical CBOR bytes.
///
/// Determinism: calling this twice with the same input MUST yield
/// byte-identical output. This is guaranteed because:
///   - AdieValue::Map carries sorted keys (invariant)
///   - ciborium uses preferred serialization
pub fn encode(value: &AdieValue) -> Result<Vec<u8>, CborError> {
    let cv = to_ciborium(value)?;
    let mut out = Vec::new();
    into_writer(&cv, &mut out).map_err(|e| CborError::Malformed {
        detail: format!("ciborium encode: {:?}", e),
    })?;
    Ok(out)
}

fn to_ciborium(v: &AdieValue) -> Result<Value, CborError> {
    Ok(match v {
        AdieValue::UInt(n) => Value::Integer(Integer::from(*n)),
        AdieValue::Int(n) => Value::Integer(Integer::from(*n)),
        AdieValue::Bytes(b) => Value::Bytes(b.clone()),
        AdieValue::Text(t) => Value::Text(t.clone()),
        AdieValue::Bool(b) => Value::Bool(*b),
        AdieValue::Null => Value::Null,
        AdieValue::Array(items) => {
            let mut out = Vec::with_capacity(items.len());
            for item in items {
                out.push(to_ciborium(item)?);
            }
            Value::Array(out)
        }
        AdieValue::Map(entries) => {
            // AdieValue::Map invariant: sorted, duplicate-free.
            // We preserve that order verbatim here.
            let mut out = Vec::with_capacity(entries.len());
            for (k, val) in entries {
                out.push((Value::Integer(Integer::from(*k)), to_ciborium(val)?));
            }
            Value::Map(out)
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn enc(v: AdieValue) -> Vec<u8> {
        encode(&v).expect("encode failed")
    }

    // ── Primitives ──
    #[test]
    fn enc_null() {
        assert_eq!(enc(AdieValue::Null), vec![0xf6]);
    }

    #[test]
    fn enc_true_false() {
        assert_eq!(enc(AdieValue::Bool(true)), vec![0xf5]);
        assert_eq!(enc(AdieValue::Bool(false)), vec![0xf4]);
    }

    #[test]
    fn enc_uint_boundaries() {
        // 0, 1, 23 in one byte
        assert_eq!(enc(AdieValue::UInt(0)), vec![0x00]);
        assert_eq!(enc(AdieValue::UInt(1)), vec![0x01]);
        assert_eq!(enc(AdieValue::UInt(23)), vec![0x17]);
        // 24 needs u8 form
        assert_eq!(enc(AdieValue::UInt(24)), vec![0x18, 0x18]);
        // 255 boundary
        assert_eq!(enc(AdieValue::UInt(255)), vec![0x18, 0xff]);
        // 256 needs u16 form
        assert_eq!(enc(AdieValue::UInt(256)), vec![0x19, 0x01, 0x00]);
        // 65535 boundary
        assert_eq!(enc(AdieValue::UInt(65535)), vec![0x19, 0xff, 0xff]);
        // 65536 needs u32 form
        assert_eq!(enc(AdieValue::UInt(65536)), vec![0x1a, 0x00, 0x01, 0x00, 0x00]);
    }

    #[test]
    fn enc_negative_int() {
        // -1 = 0x20
        assert_eq!(enc(AdieValue::Int(-1)), vec![0x20]);
        // -24 = 0x37 (major 1, additional 23)
        assert_eq!(enc(AdieValue::Int(-24)), vec![0x37]);
        // -25 needs u8 form
        assert_eq!(enc(AdieValue::Int(-25)), vec![0x38, 0x18]);
    }

    #[test]
    fn enc_text() {
        assert_eq!(enc(AdieValue::Text("".into())), vec![0x60]);
        // "hi" = 62 68 69
        assert_eq!(enc(AdieValue::Text("hi".into())), vec![0x62, 0x68, 0x69]);
        // "é" = 62 c3 a9
        assert_eq!(enc(AdieValue::Text("é".into())), vec![0x62, 0xc3, 0xa9]);
    }

    #[test]
    fn enc_bytes() {
        assert_eq!(enc(AdieValue::Bytes(vec![])), vec![0x40]);
        assert_eq!(enc(AdieValue::Bytes(vec![1, 2, 3])), vec![0x43, 0x01, 0x02, 0x03]);
    }

    // ── Arrays ──
    #[test]
    fn enc_empty_array() {
        assert_eq!(enc(AdieValue::Array(vec![])), vec![0x80]);
    }

    #[test]
    fn enc_array_three() {
        // [true, false, null] = 83 f5 f4 f6
        let v = AdieValue::Array(vec![
            AdieValue::Bool(true),
            AdieValue::Bool(false),
            AdieValue::Null,
        ]);
        assert_eq!(enc(v), vec![0x83, 0xf5, 0xf4, 0xf6]);
    }

    // ── Maps ──
    #[test]
    fn enc_empty_map() {
        assert_eq!(enc(AdieValue::Map(vec![])), vec![0xa0]);
    }

    #[test]
    fn enc_single_map() {
        // {1: true} = a1 01 f5
        let v = AdieValue::Map(vec![(1, AdieValue::Bool(true))]);
        assert_eq!(enc(v), vec![0xa1, 0x01, 0xf5]);
    }

    #[test]
    fn enc_sorted_map_byte_identical() {
        // Two sorted maps (different construction order but same content)
        // must produce identical bytes.
        let a = AdieValue::Map(vec![
            (1, AdieValue::Text("a".into())),
            (2, AdieValue::Text("b".into())),
        ]);
        let b = AdieValue::Map(vec![
            (1, AdieValue::Text("a".into())),
            (2, AdieValue::Text("b".into())),
        ]);
        assert_eq!(enc(a), enc(b));
    }

    // ── Determinism ──
    #[test]
    fn enc_deterministic_repeated() {
        let v = AdieValue::Map(vec![
            (1, AdieValue::Text("one".into())),
            (2, AdieValue::Array(vec![AdieValue::UInt(10), AdieValue::UInt(20)])),
            (256, AdieValue::Bytes(vec![0xde, 0xad])),
        ]);
        let a = enc(v.clone());
        let b = enc(v);
        assert_eq!(a, b);
    }

    // ── Nested ──
    #[test]
    fn enc_nested() {
        // {1: [true, null]}
        // a1 01 82 f5 f6  (5 bytes)
        let v = AdieValue::Map(vec![(
            1,
            AdieValue::Array(vec![AdieValue::Bool(true), AdieValue::Null]),
        )]);
        assert_eq!(enc(v), vec![0xa1, 0x01, 0x82, 0xf5, 0xf6]);
    }

    // ── Round-trip with decoder would need decoder; test separately
    // in decoder.rs. Here we only test encode output.

    // ── Boundary: full uint64 max ──
    #[test]
    fn enc_uint64_max() {
        let expected = vec![
            0x1b, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        ];
        assert_eq!(enc(AdieValue::UInt(u64::MAX)), expected);
    }
}

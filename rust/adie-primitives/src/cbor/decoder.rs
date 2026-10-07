//! ADIE strict CBOR decoder (Phase 3, Gate 1, 3A.2).
//!
//! Normative source: WIRE-FORMAT-0.2 §7, §8, §9.
//!
//! Pipeline (in order):
//!   1. rawcheck::scan_top_level   -- byte-level structure
//!   2. ciborium::de::from_reader  -- parse to Value
//!   3. profile::validate          -- profile authority
//!   4. encoder::encode            -- canonical re-encode
//!   5. bytewise comparison        -- canonicality of the input
//!
//! Each layer catches a distinct class of violation:
//!   - rawcheck: no trailing bytes, definite lengths, no floats/tags,
//!               shortest integer and length encodings
//!   - profile:  integer keys only, sorted, deduplicated, valid types
//!   - encoder:  re-emits canonical form
//!   - comparison: catches unsorted map keys (the only remaining
//!                 divergence after rawcheck + profile)
//!
//! The decoder is NOT the sole authority: rawcheck, profile, and the
//! encoder each enforce a slice of WIRE-FORMAT-0.2.

use ciborium::de::from_reader;

use crate::cbor::error::CborError;
use crate::cbor::profile;
use crate::cbor::rawcheck;
use crate::cbor::value::AdieValue;
use crate::cbor::encoder;

/// Decode CBOR bytes into an `AdieValue`.
///
/// Rejects every non-canonical, malformed, or out-of-profile input
/// with a specific error code (WIRE-FORMAT-0.2 §9).
pub fn decode(bytes: &[u8]) -> Result<AdieValue, CborError> {
    // 1. Raw-byte structural validation. Also rejects trailing bytes.
    rawcheck::scan_top_level(bytes)?;

    // 2. Parse to ciborium::Value. ciborium consumes one top-level
    //    item; we already know there are no trailing bytes.
    let mut cursor = std::io::Cursor::new(bytes);
    let cv: ciborium::value::Value =
        from_reader(&mut cursor).map_err(|e| CborError::Malformed {
            detail: format!("ciborium parse: {:?}", e),
        })?;

    // 3. Profile validation. Returns AdieValue with maps sorted and
    //    duplicate-free; rejects forbidden types and unknown variants.
    let av = profile::validate(&cv)?;

    // 4. Canonical re-encode.
    let re_encoded = encoder::encode(&av)?;

    // 5. Bytewise comparison. After rawcheck (shortest encodings) and
    //    profile (sorted maps), the only possible divergence is an
    //    unsorted map in the input. That is exactly what
    //    E_WIRE_NONCANONICAL_MAP identifies.
    if re_encoded.as_slice() != bytes {
        return Err(CborError::NonCanonicalMap);
    }

    Ok(av)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hx(b: &[u8]) -> String {
        b.iter().map(|x| format!("{:02x}", x)).collect()
    }

    fn ok(bytes: &[u8]) -> AdieValue {
        decode(bytes).unwrap_or_else(|e| panic!("decode failed: {} on {}", e, hx(bytes)))
    }

    fn expect_err(bytes: &[u8]) -> CborError {
        match decode(bytes) {
            Ok(v) => panic!("expected error, got {:?}", v),
            Err(e) => e,
        }
    }

    // ── Valid round-trips ──
    #[test]
    fn dec_null() {
        assert_eq!(ok(&[0xf6]), AdieValue::Null);
    }

    #[test]
    fn dec_true_false() {
        assert_eq!(ok(&[0xf5]), AdieValue::Bool(true));
        assert_eq!(ok(&[0xf4]), AdieValue::Bool(false));
    }

    #[test]
    fn dec_uint_boundaries() {
        assert_eq!(ok(&[0x00]), AdieValue::UInt(0));
        assert_eq!(ok(&[0x17]), AdieValue::UInt(23));
        assert_eq!(ok(&[0x18, 0x18]), AdieValue::UInt(24));
        assert_eq!(ok(&[0x18, 0xff]), AdieValue::UInt(255));
        assert_eq!(ok(&[0x19, 0x01, 0x00]), AdieValue::UInt(256));
        assert_eq!(ok(&[0x19, 0xff, 0xff]), AdieValue::UInt(65535));
        assert_eq!(ok(&[0x1a, 0x00, 0x01, 0x00, 0x00]), AdieValue::UInt(65536));
    }

    #[test]
    fn dec_negative_int() {
        assert_eq!(ok(&[0x20]), AdieValue::Int(-1));
        assert_eq!(ok(&[0x37]), AdieValue::Int(-24));
        assert_eq!(ok(&[0x38, 0x18]), AdieValue::Int(-25));
    }

    #[test]
    fn dec_text() {
        assert_eq!(ok(&[0x60]), AdieValue::Text("".into()));
        assert_eq!(ok(&[0x62, 0x68, 0x69]), AdieValue::Text("hi".into()));
        assert_eq!(ok(&[0x62, 0xc3, 0xa9]), AdieValue::Text("é".into()));
    }

    #[test]
    fn dec_bytes() {
        assert_eq!(ok(&[0x40]), AdieValue::Bytes(vec![]));
        assert_eq!(ok(&[0x43, 0x01, 0x02, 0x03]), AdieValue::Bytes(vec![1, 2, 3]));
    }

    #[test]
    fn dec_empty_array_map() {
        assert_eq!(ok(&[0x80]), AdieValue::Array(vec![]));
        assert_eq!(ok(&[0xa0]), AdieValue::Map(vec![]));
    }

    #[test]
    fn dec_single_map() {
        let v = ok(&[0xa1, 0x01, 0xf5]);
        assert_eq!(v, AdieValue::Map(vec![(1, AdieValue::Bool(true))]));
    }

    #[test]
    fn dec_sorted_two_entry_map() {
        // a2 01 61 61 02 61 62 = {1:"a", 2:"b"}
        let v = ok(&[0xa2, 0x01, 0x61, 0x61, 0x02, 0x61, 0x62]);
        if let AdieValue::Map(entries) = v {
            assert_eq!(entries.len(), 2);
            assert_eq!(entries[0].0, 1);
            assert_eq!(entries[1].0, 2);
        } else {
            panic!("expected map");
        }
    }

    #[test]
    fn dec_nested() {
        // a1 01 82 f5 f6 = {1: [true, null]}
        let v = ok(&[0xa1, 0x01, 0x82, 0xf5, 0xf6]);
        if let AdieValue::Map(entries) = v {
            assert_eq!(entries.len(), 1);
            if let AdieValue::Array(arr) = &entries[0].1 {
                assert_eq!(arr.len(), 2);
            } else {
                panic!();
            }
        } else {
            panic!();
        }
    }

    // ── Malformed ──
    #[test]
    fn dec_empty_input_rejected() {
        expect_err(&[]);
    }

    #[test]
    fn dec_truncated_rejected() {
        expect_err(&[0x43, 0x01, 0x02]);
    }

    // ── Trailing ──
    #[test]
    fn dec_trailing_rejected() {
        match expect_err(&[0xf6, 0x00]) {
            CborError::Trailing { extra } => assert_eq!(extra, 1),
            e => panic!("expected Trailing, got {:?}", e),
        }
    }

    // ── Indefinite ──
    #[test]
    fn dec_indefinite_map_rejected() {
        match expect_err(&[0xbf, 0x01, 0x61, 0x78, 0xff]) {
            CborError::Indefinite => {}
            e => panic!("expected Indefinite, got {:?}", e),
        }
    }

    #[test]
    fn dec_indefinite_array_rejected() {
        match expect_err(&[0x9f, 0x01, 0xff]) {
            CborError::Indefinite => {}
            e => panic!("expected Indefinite, got {:?}", e),
        }
    }

    // ── Floats ──
    #[test]
    fn dec_float16_rejected() {
        match expect_err(&[0xf9, 0x3c, 0x00]) {
            CborError::Float => {}
            e => panic!("expected Float, got {:?}", e),
        }
    }

    #[test]
    fn dec_float64_rejected() {
        match expect_err(&[0xfb, 0x3f, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) {
            CborError::Float => {}
            e => panic!("expected Float, got {:?}", e),
        }
    }

    // ── Tags ──
    #[test]
    fn dec_tag_rejected() {
        match expect_err(&[0xc1, 0x01]) {
            CborError::Tag { tag } => assert_eq!(tag, 1),
            e => panic!("expected Tag, got {:?}", e),
        }
    }

    // ── Non-canonical integers ──
    #[test]
    fn dec_noncanonical_int_rejected() {
        match expect_err(&[0x18, 0x01]) {
            CborError::NonCanonicalInt => {}
            e => panic!("expected NonCanonicalInt, got {:?}", e),
        }
    }

    #[test]
    fn dec_noncanonical_length_prefix_rejected() {
        // 58 01 78 = byte string of length 1 with u8 length prefix
        match expect_err(&[0x58, 0x01, 0x78]) {
            CborError::NonCanonicalInt => {}
            e => panic!("expected NonCanonicalInt, got {:?}", e),
        }
    }

    // ── Duplicate keys ──
    #[test]
    fn dec_duplicate_keys_rejected() {
        // a2 01 61 61 01 61 62 = {1:"a", 1:"b"}
        match expect_err(&[0xa2, 0x01, 0x61, 0x61, 0x01, 0x61, 0x62]) {
            CborError::DuplicateKey => {}
            e => panic!("expected DuplicateKey, got {:?}", e),
        }
    }

    // ── Unsorted map keys ──
    #[test]
    fn dec_unsorted_map_rejected() {
        // a2 02 61 62 01 61 61 = {2:"b", 1:"a"} (unsorted)
        match expect_err(&[0xa2, 0x02, 0x61, 0x62, 0x01, 0x61, 0x61]) {
            CborError::NonCanonicalMap => {}
            e => panic!("expected NonCanonicalMap, got {:?}", e),
        }
    }

    // ── Wrong key types ──
    #[test]
    fn dec_text_key_rejected() {
        // a1 61 61 01 = {"a": 1}
        match expect_err(&[0xa1, 0x61, 0x61, 0x01]) {
            CborError::TypeMismatch { .. } => {}
            e => panic!("expected TypeMismatch, got {:?}", e),
        }
    }

    #[test]
    fn dec_bytes_key_rejected() {
        // a1 41 61 01 = {h'61': 1}
        match expect_err(&[0xa1, 0x41, 0x61, 0x01]) {
            CborError::TypeMismatch { .. } => {}
            e => panic!("expected TypeMismatch, got {:?}", e),
        }
    }

    // ── Undefined ──
    #[test]
    fn dec_undefined_rejected() {
        match expect_err(&[0xf7]) {
            CborError::Malformed { .. } => {}
            e => panic!("expected Malformed, got {:?}", e),
        }
    }

    // ── Invalid UTF-8 ──
    #[test]
    fn dec_invalid_utf8_rejected() {
        match expect_err(&[0x62, 0xff, 0xfe]) {
            CborError::InvalidUtf8 => {}
            e => panic!("expected InvalidUtf8, got {:?}", e),
        }
    }

    // ── Round-trip: encode(decode(b)) == b for canonical b ──
    #[test]
    fn dec_enc_roundtrip_bytes_stable() {
        let canonical = vec![
            // {1: [true, null], 2: "hi", 256: h'01 02 03'}
            0xa3,
            0x01, 0x82, 0xf5, 0xf6,
            0x02, 0x62, 0x68, 0x69,
            0x19, 0x01, 0x00, 0x43, 0x01, 0x02, 0x03,
        ];
        let v = ok(&canonical);
        let re = encoder::encode(&v).unwrap();
        assert_eq!(re, canonical);
    }

    // ── Round-trip: decode(encode(v)) == v ──
    #[test]
    fn dec_enc_roundtrip_value_stable() {
        let v = AdieValue::Map(vec![
            (1, AdieValue::Text("a".into())),
            (24, AdieValue::Array(vec![AdieValue::Bool(true), AdieValue::Null])),
            (256, AdieValue::Bytes(vec![0xde, 0xad, 0xbe, 0xef])),
        ]);
        let bytes = encoder::encode(&v).unwrap();
        let v2 = ok(&bytes);
        assert_eq!(v, v2);
    }

    // ── Full end-to-end: encode then decode then compare ──
    #[test]
    fn dec_deterministic_bytes() {
        let v = AdieValue::Map(vec![
            (1, AdieValue::UInt(u64::MAX)),
            (2, AdieValue::Int(-1)),
            (65536, AdieValue::Text("big".into())),
        ]);
        let a = encoder::encode(&v).unwrap();
        let b = encoder::encode(&ok(&a)).unwrap();
        assert_eq!(a, b);
    }
}

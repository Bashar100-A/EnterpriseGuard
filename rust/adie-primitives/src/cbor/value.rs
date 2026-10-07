//! ADIE value model (Phase 3, Gate 1, 3A.2).
//!
//! This is a **profile type system**, not a CBOR type system.
//! Types not appearing here are not admitted by DCP 2.1.
//! ciborium's Value can represent more (Float, Tag, indefinite), but
//! ADIE rejects those during decoding (WIRE-FORMAT-0.2 §7).
//!
//! Map keys: unsigned integers only, encoded in shortest form,
//! sorted by RFC 8949 bytewise lexicographic order of their
//! deterministic encodings.

use crate::cbor::error::CborError;

/// Value admissible by the ADIE DCP 2.1 profile.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdieValue {
    UInt(u64),
    Int(i64),
    Bytes(Vec<u8>),
    Text(String),
    Array(Vec<AdieValue>),
    /// Map with unsigned-integer keys only, in canonical order.
    Map(Vec<(u64, AdieValue)>),
    Bool(bool),
    Null,
}

/// Minimal CBOR integer encoding for a u64 (major type 0).
///
/// Follows RFC 8949 §3.4.3 preferred serialization: shortest form.
pub fn encode_uint_shortest(n: u64) -> Vec<u8> {
    if n < 24 {
        vec![n as u8]
    } else if n <= 0xFF {
        vec![0x18, n as u8]
    } else if n <= 0xFFFF {
        vec![0x19, (n >> 8) as u8, (n & 0xFF) as u8]
    } else if n <= 0xFFFF_FFFF {
        let b = n.to_be_bytes();
        vec![0x1A, b[4], b[5], b[6], b[7]]
    } else {
        let b = n.to_be_bytes();
        vec![0x1B, b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]]
    }
}

/// Compare two u64 values by RFC 8949 bytewise lexicographic order of
/// their deterministic (shortest-form) CBOR encodings.
///
/// This is the normative ordering required by WIRE-FORMAT-0.2 §8 rule 2.
///
/// Concretely: compare encoded bytes, and if prefixes are equal, the
/// shorter encoding comes first. But since we encode the whole integer
/// at once, comparing byte vectors with Rust's `Ord` yields the same
/// result as the RFC's bytewise lexicographic rule.
pub fn cmp_uint_rfc8949(a: u64, b: u64) -> core::cmp::Ordering {
    let ea = encode_uint_shortest(a);
    let eb = encode_uint_shortest(b);
    ea.cmp(&eb)
}

/// Sort a map's entries by RFC 8949 order and reject duplicate keys.
///
/// Duplicate key rejection MUST happen before this function returns
/// (WIRE-FORMAT-0.2 §3, and Commander order §3).
pub fn canonicalize_map(
    mut entries: Vec<(u64, AdieValue)>,
) -> Result<Vec<(u64, AdieValue)>, CborError> {
    entries.sort_by(|a, b| cmp_uint_rfc8949(a.0, b.0));

    // Duplicate detection after sorting (adjacent equal keys).
    for w in entries.windows(2) {
        if w[0].0 == w[1].0 {
            return Err(CborError::DuplicateKey);
        }
    }

    Ok(entries)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Boundary tests for encoding (Commander order §6) ──
    #[test]
    fn encode_boundaries() {
        // RFC 8949 §3.4.3 canonical integer encoding
        assert_eq!(encode_uint_shortest(0), vec![0x00]);
        assert_eq!(encode_uint_shortest(1), vec![0x01]);
        assert_eq!(encode_uint_shortest(23), vec![0x17]);
        assert_eq!(encode_uint_shortest(24), vec![0x18, 0x18]);
        assert_eq!(encode_uint_shortest(25), vec![0x18, 0x19]);
        assert_eq!(encode_uint_shortest(255), vec![0x18, 0xFF]);
        assert_eq!(encode_uint_shortest(256), vec![0x19, 0x01, 0x00]);
        assert_eq!(encode_uint_shortest(257), vec![0x19, 0x01, 0x01]);
        assert_eq!(encode_uint_shortest(65535), vec![0x19, 0xFF, 0xFF]);
        assert_eq!(encode_uint_shortest(65536), vec![0x1A, 0x00, 0x01, 0x00, 0x00]);
        assert_eq!(encode_uint_shortest(u32::MAX as u64),
                   vec![0x1A, 0xFF, 0xFF, 0xFF, 0xFF]);
        assert_eq!(encode_uint_shortest(u64::MAX),
                   vec![0x1B, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]);
    }

    // ── RFC 8949 order tests: must differ from pure numeric for some pairs ──
    #[test]
    fn rfc_order_is_length_then_bytewise() {
        // Numeric ascending: 24 < 255 < 256
        // Encoded: [18 18] < [18 FF] < [19 01 00]
        // Bytewise lexicographic: [18 18] < [18 FF] < [19 01 00] — same
        assert_eq!(cmp_uint_rfc8949(24, 255), core::cmp::Ordering::Less);
        assert_eq!(cmp_uint_rfc8949(255, 256), core::cmp::Ordering::Less);
        // The interesting case: shorter encoding always wins as a prefix,
        // even though numerically the shorter value is smaller anyway.
        assert_eq!(cmp_uint_rfc8949(23, 24), core::cmp::Ordering::Less);
    }

    #[test]
    fn rfc_order_full_boundary_sweep() {
        let bounds = [0u64, 1, 23, 24, 25, 255, 256, 257, 65535, 65536,
                      0xFFFF_FFFF, 0x1_0000_0000, u64::MAX];
        for i in 0..bounds.len() {
            for j in (i + 1)..bounds.len() {
                assert_eq!(cmp_uint_rfc8949(bounds[i], bounds[j]),
                           core::cmp::Ordering::Less,
                           "expected {} < {}", bounds[i], bounds[j]);
            }
        }
    }

    #[test]
    fn canonicalize_map_sorts_correctly() {
        let entries = vec![
            (256u64, AdieValue::Text("c".into())),
            (24u64,  AdieValue::Text("a".into())),
            (255u64, AdieValue::Text("b".into())),
        ];
        let sorted = canonicalize_map(entries).unwrap();
        assert_eq!(sorted[0].0, 24);
        assert_eq!(sorted[1].0, 255);
        assert_eq!(sorted[2].0, 256);
    }

    #[test]
    fn canonicalize_map_rejects_duplicates() {
        let entries = vec![
            (1u64, AdieValue::Text("a".into())),
            (2u64, AdieValue::Text("b".into())),
            (1u64, AdieValue::Text("c".into())),
        ];
        let r = canonicalize_map(entries);
        assert!(matches!(r, Err(CborError::DuplicateKey)));
    }

    #[test]
    fn canonicalize_map_empty_ok() {
        let sorted = canonicalize_map(vec![]).unwrap();
        assert!(sorted.is_empty());
    }

    #[test]
    fn canonicalize_map_already_sorted_ok() {
        let entries = vec![
            (0u64, AdieValue::Null),
            (24u64, AdieValue::Bool(true)),
            (256u64, AdieValue::UInt(99)),
        ];
        let sorted = canonicalize_map(entries).unwrap();
        assert_eq!(sorted.len(), 3);
        assert_eq!(sorted[0].0, 0);
        assert_eq!(sorted[1].0, 24);
        assert_eq!(sorted[2].0, 256);
    }

    #[test]
    fn adie_value_equality() {
        assert_eq!(AdieValue::UInt(1), AdieValue::UInt(1));
        assert_ne!(AdieValue::UInt(1), AdieValue::Int(1));
        assert_eq!(AdieValue::Null, AdieValue::Null);
        assert_ne!(AdieValue::Bool(true), AdieValue::Bool(false));
    }
}

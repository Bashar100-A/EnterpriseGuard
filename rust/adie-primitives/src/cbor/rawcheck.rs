//! ADIE raw-byte structural pre-check (Phase 3, Gate 1, 3A.2).
//!
//! Runs BEFORE ciborium. ciborium collapses indefinite-length items
//! and does not report them; this module rejects them on raw bytes.
//! It also detects trailing bytes after the top-level item.
//!
//! Normative source: WIRE-FORMAT-0.2 §7 (forbidden types), §8 (rule 3,
//! rule 8), §9 (codes).
//!
//! This is a structural scanner: it does not construct a value tree.
//! It walks the CBOR grammar, enforcing:
//!   - no indefinite-length items
//!   - no tags (major type 6)
//!   - no floats (major type 7, additional 25/26/27)
//!   - no undefined (0xF7)
//!   - no non-shortest integer or length encodings
//!   - no trailing bytes at the top level
//!   - depth ≤ 32

use crate::cbor::error::CborError;

pub const MAX_DEPTH: usize = 32;

/// Scan a top-level CBOR item starting at offset 0 in `bytes`.
///
/// On success, returns the number of bytes consumed by the item.
/// The caller MUST verify that `consumed == bytes.len()`;
/// otherwise it is a trailing-bytes error.
pub fn scan_top_level(bytes: &[u8]) -> Result<usize, CborError> {
    let (consumed, _) = scan_item(bytes, 0, 0)?;
    if consumed != bytes.len() {
        return Err(CborError::Trailing {
            extra: bytes.len() - consumed,
        });
    }
    Ok(consumed)
}

// ──────────────────────────────────────────────────────────────
// Internal helpers
// ──────────────────────────────────────────────────────────────

fn read_u8(bytes: &[u8], offset: usize) -> Result<u8, CborError> {
    bytes.get(offset).copied().ok_or_else(|| CborError::Malformed {
        detail: format!("unexpected end of input at offset {}", offset),
    })
}

fn read_bytes(bytes: &[u8], offset: usize, n: usize) -> Result<&[u8], CborError> {
    let end = offset
        .checked_add(n)
        .ok_or_else(|| CborError::Malformed { detail: "length overflow".into() })?;
    bytes
        .get(offset..end)
        .ok_or_else(|| CborError::Malformed {
            detail: format!("unexpected end of input: need {} bytes at offset {}", n, offset),
        })
}

/// Read a CBOR length (for byte strings, text strings, arrays, maps).
/// Enforces shortest form and rejects indefinite (additional 31).
/// Returns (length, new_offset).
fn read_length(bytes: &[u8], offset: usize, additional: u8) -> Result<(u64, usize), CborError> {
    match additional {
        0..=23 => Ok((additional as u64, offset + 1)),
        24 => {
            let b = read_u8(bytes, offset + 1)?;
            if b < 24 {
                return Err(CborError::NonCanonicalInt);
            }
            Ok((b as u64, offset + 2))
        }
        25 => {
            let raw = read_bytes(bytes, offset + 1, 2)?;
            let n = u16::from_be_bytes([raw[0], raw[1]]) as u64;
            if n < 256 {
                return Err(CborError::NonCanonicalInt);
            }
            Ok((n, offset + 3))
        }
        26 => {
            let raw = read_bytes(bytes, offset + 1, 4)?;
            let n = u32::from_be_bytes([raw[0], raw[1], raw[2], raw[3]]) as u64;
            if n < 65536 {
                return Err(CborError::NonCanonicalInt);
            }
            Ok((n, offset + 5))
        }
        27 => {
            let raw = read_bytes(bytes, offset + 1, 8)?;
            let n = u64::from_be_bytes([
                raw[0], raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7],
            ]);
            if n < 0x1_0000_0000 {
                return Err(CborError::NonCanonicalInt);
            }
            Ok((n, offset + 9))
        }
        28..=30 => Err(CborError::Malformed {
            detail: format!("reserved additional info {}", additional),
        }),
        31 => Err(CborError::Indefinite),
        _ => Err(CborError::Malformed {
            detail: format!("invalid additional info {}", additional),
        }),
    }
}

/// Extract the byte range of an item starting at `offset` by walking
/// the CBOR grammar recursively (without constructing a value tree).
/// Used for duplicate-key detection inside maps.
fn scan_item_range(bytes: &[u8], offset: usize, depth: usize) -> Result<usize, CborError> {
    let (next, _) = scan_item(bytes, offset, depth)?;
    Ok(next)
}

/// Walk a map body (n keys, n values) and reject duplicate keys.
/// Duplicate = byte-identical encoded key. This matches the
/// DEFECT-027 principle: rawcheck rejects wire-level constructs whose
/// semantic type would be erased by decoding.
fn scan_map_body(
    bytes: &[u8],
    offset: usize,
    n: u64,
    depth: usize,
) -> Result<usize, CborError> {
    let mut cur = offset;
    let mut key_ranges: Vec<(usize, usize)> = Vec::with_capacity((n as usize).min(4096));
    for _ in 0..n {
        let k_start = cur;
        cur = scan_item_range(bytes, cur, depth)?;
        let k_end = cur;
        for &(ps, pe) in &key_ranges {
            if pe - ps == k_end - k_start {
                if &bytes[ps..pe] == &bytes[k_start..k_end] {
                    return Err(CborError::DuplicateKey);
                }
            }
        }
        key_ranges.push((k_start, k_end));
        cur = scan_item_range(bytes, cur, depth)?;
    }
    Ok(cur)
}

/// Scan a single CBOR item at `offset`. Returns (new_offset, depth_of_item).
/// Depth tracking is only meaningful for container types; leaf types
/// return the passed-in depth.
fn scan_item(bytes: &[u8], offset: usize, depth: usize) -> Result<(usize, usize), CborError> {
    if depth > MAX_DEPTH {
        return Err(CborError::Malformed {
            detail: format!("max nesting depth {} exceeded", MAX_DEPTH),
        });
    }

    let head = read_u8(bytes, offset)?;
    let major = head >> 5;
    let additional = head & 0x1F;

    match major {
        // 0: unsigned integer. Must be shortest form.
        0 => {
            let (_, next) = read_length(bytes, offset, additional)?;
            Ok((next, depth))
        }
        // 1: negative integer. Same shortest-form rule.
        1 => {
            let (_, next) = read_length(bytes, offset, additional)?;
            Ok((next, depth))
        }
        // 2: byte string.
        2 => {
            let (len, next) = read_length(bytes, offset, additional)?;
            let next_usize = usize::try_from(len).map_err(|_| CborError::Malformed {
                detail: "byte string length exceeds addressable range".into(),
            })?;
            // Verify the payload is present.
            read_bytes(bytes, next, next_usize)?;
            Ok((next + next_usize, depth))
        }
        // 3: text string.
        3 => {
            let (len, next) = read_length(bytes, offset, additional)?;
            let next_usize = usize::try_from(len).map_err(|_| CborError::Malformed {
                detail: "text string length exceeds addressable range".into(),
            })?;
            let payload = read_bytes(bytes, next, next_usize)?;
            // Enforce valid UTF-8.
            if core::str::from_utf8(payload).is_err() {
                return Err(CborError::InvalidUtf8);
            }
            Ok((next + next_usize, depth))
        }
        // 4: array.
        4 => {
            let (count, next) = read_length(bytes, offset, additional)?;
            let mut cursor = next;
            for _ in 0..count {
                let (new_cursor, _) = scan_item(bytes, cursor, depth + 1)?;
                cursor = new_cursor;
            }
            Ok((cursor, depth))
        }
        // 5: map. Keys and values are each scanned as items; duplicate
        // keys (byte-identical encodings) are rejected here so the wire
        // layer preserves that fact before any decoder deduplicates.
        // See DEFECT-027 (JS) and DEFECT-036 (cross-runtime parity).
        5 => {
            let (count, next) = read_length(bytes, offset, additional)?;
            let cursor = scan_map_body(bytes, next, count, depth + 1)?;
            Ok((cursor, depth))
        }
        // 6: tag — forbidden.
        6 => {
            let (tag, _) = read_length(bytes, offset, additional)?;
            Err(CborError::Tag { tag })
        }
        // 7: simple values and floats.
        7 => match additional {
            // Simple values 0..=19 are reserved/undefined in most profiles.
            // We accept only: false (20), true (21), null (22).
            20 | 21 | 22 => Ok((offset + 1, depth)),
            // 23 = "undefined". Forbidden.
            23 => Err(CborError::Malformed {
                detail: "undefined (0xF7) is not permitted".into(),
            }),
            // 24: simple value (u8 next byte).
            24 => {
                let _ = read_u8(bytes, offset + 1)?;
                Err(CborError::Malformed {
                    detail: "simple value with 1-byte argument is not permitted".into(),
                })
            }
            // 25: float16, 26: float32, 27: float64.
            25 | 26 | 27 => Err(CborError::Float),
            // 28..=30 reserved, 31 is break (only inside indefinite).
            28..=30 => Err(CborError::Malformed {
                detail: format!("reserved simple-value additional {}", additional),
            }),
            31 => Err(CborError::Malformed {
                detail: "stray break (0xFF) outside indefinite container".into(),
            }),
            // 0..=19: unassigned simple values.
            _ => Err(CborError::Malformed {
                detail: format!("simple value {} is not permitted", additional),
            }),
        },
        _ => unreachable!(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ok(bytes: &[u8]) -> usize {
        scan_top_level(bytes).expect("expected OK")
    }

    fn err(bytes: &[u8]) -> CborError {
        scan_top_level(bytes).expect_err("expected error")
    }

    // ── Valid primitives ──
    #[test]
    fn valid_null() {
        assert_eq!(ok(&[0xf6]), 1);
    }

    #[test]
    fn valid_true_false() {
        assert_eq!(ok(&[0xf5]), 1); // true
        assert_eq!(ok(&[0xf4]), 1); // false
    }

    #[test]
    fn valid_uint_small() {
        assert_eq!(ok(&[0x00]), 1);        // 0
        assert_eq!(ok(&[0x01]), 1);        // 1
        assert_eq!(ok(&[0x17]), 1);        // 23
        assert_eq!(ok(&[0x18, 0x18]), 2);  // 24 (u8 form)
        assert_eq!(ok(&[0x19, 0x01, 0x00]), 3); // 256 (u16)
    }

    #[test]
    fn valid_negative_int() {
        assert_eq!(ok(&[0x20]), 1);        // -1
        assert_eq!(ok(&[0x37]), 1);        // -24
        assert_eq!(ok(&[0x38, 0x18]), 2);  // -25
    }

    #[test]
    fn valid_empty_bytes_text() {
        assert_eq!(ok(&[0x40]), 1);        // empty byte string
        assert_eq!(ok(&[0x60]), 1);        // empty text string
    }

    #[test]
    fn valid_bytes_payload() {
        assert_eq!(ok(&[0x43, 0x01, 0x02, 0x03]), 4);
    }

    #[test]
    fn valid_text_payload() {
        // "hi" = 62 68 69
        assert_eq!(ok(&[0x62, 0x68, 0x69]), 3);
    }

    #[test]
    fn valid_empty_array_map() {
        assert_eq!(ok(&[0x80]), 1); // empty array
        assert_eq!(ok(&[0xa0]), 1); // empty map
    }

    #[test]
    fn valid_nested() {
        // {1: [true, null]}
        // a1 01 82 f5 f6
        // Bytes: a1 (map, 1 entry) + 01 (key) + 82 (array, 2 items)
        //        + f5 (true) + f6 (null) = 5 bytes.
        assert_eq!(ok(&[0xa1, 0x01, 0x82, 0xf5, 0xf6]), 5);
    }

    // ── Trailing bytes ──
    #[test]
    fn trailing_after_null() {
        match err(&[0xf6, 0x00]) {
            CborError::Trailing { extra } => assert_eq!(extra, 1),
            e => panic!("expected Trailing, got {:?}", e),
        }
    }

    #[test]
    fn trailing_after_map() {
        // a0 ff  — map {} followed by stray 0xff
        match err(&[0xa0, 0xff]) {
            CborError::Trailing { extra } => assert_eq!(extra, 1),
            e => panic!("expected Trailing, got {:?}", e),
        }
    }

    // ── Indefinite-length items ──
    #[test]
    fn indefinite_map() {
        // bf 01 61 78 ff
        assert!(matches!(err(&[0xbf, 0x01, 0x61, 0x78, 0xff]),
                         CborError::Indefinite));
    }

    #[test]
    fn indefinite_array() {
        // 9f 01 ff
        assert!(matches!(err(&[0x9f, 0x01, 0xff]),
                         CborError::Indefinite));
    }

    #[test]
    fn indefinite_bytes() {
        // 5f 41 78 ff
        assert!(matches!(err(&[0x5f, 0x41, 0x78, 0xff]),
                         CborError::Indefinite));
    }

    #[test]
    fn indefinite_text() {
        // 7f 61 78 ff
        assert!(matches!(err(&[0x7f, 0x61, 0x78, 0xff]),
                         CborError::Indefinite));
    }

    // ── Floats ──
    #[test]
    fn float16() {
        // f9 3c 00 = 1.0
        assert!(matches!(err(&[0xf9, 0x3c, 0x00]), CborError::Float));
    }

    #[test]
    fn float32() {
        // fa 3f 80 00 00 = 1.0
        assert!(matches!(err(&[0xfa, 0x3f, 0x80, 0x00, 0x00]), CborError::Float));
    }

    #[test]
    fn float64() {
        // fb 3f f0 00 00 00 00 00 00 = 1.0
        assert!(matches!(
            err(&[0xfb, 0x3f, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
            CborError::Float
        ));
    }

    // ── Tags ──
    #[test]
    fn tag_1() {
        // c1 01
        match err(&[0xc1, 0x01]) {
            CborError::Tag { tag } => assert_eq!(tag, 1),
            e => panic!("expected Tag, got {:?}", e),
        }
    }

    #[test]
    fn tag_bignum() {
        // d8 18 01 = tag 24
        match err(&[0xd8, 0x18, 0x01]) {
            CborError::Tag { tag } => assert_eq!(tag, 24),
            e => panic!("expected Tag, got {:?}", e),
        }
    }

    // ── Non-canonical integers ──
    #[test]
    fn noncanonical_u8_for_1() {
        // 18 01 = u8 encoding of integer 1 (should be 0x01)
        assert!(matches!(err(&[0x18, 0x01]), CborError::NonCanonicalInt));
    }

    #[test]
    fn noncanonical_u16_for_1() {
        assert!(matches!(err(&[0x19, 0x00, 0x01]), CborError::NonCanonicalInt));
    }

    #[test]
    fn noncanonical_u32_for_1() {
        assert!(matches!(
            err(&[0x1a, 0x00, 0x00, 0x00, 0x01]),
            CborError::NonCanonicalInt
        ));
    }

    #[test]
    fn noncanonical_u64_for_1() {
        assert!(matches!(
            err(&[0x1b, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]),
            CborError::NonCanonicalInt
        ));
    }

    #[test]
    fn noncanonical_bytes_length() {
        // 58 01 78 = byte string of length 1 with u8 form (should be 0x41 0x78)
        assert!(matches!(err(&[0x58, 0x01, 0x78]), CborError::NonCanonicalInt));
    }

    // ── Undefined ──
    #[test]
    fn undefined_rejected() {
        assert!(matches!(err(&[0xf7]), CborError::Malformed { .. }));
    }

    // ── Truncated input ──
    #[test]
    fn truncated_bytes() {
        // 43 01 02 — declared 3 bytes, only 2 present
        assert!(matches!(err(&[0x43, 0x01, 0x02]), CborError::Malformed { .. }));
    }

    #[test]
    fn truncated_empty() {
        assert!(matches!(err(&[]), CborError::Malformed { .. }));
    }

    // ── UTF-8 ──
    #[test]
    fn invalid_utf8_rejected() {
        // 62 ff fe — text string of 2 bytes with invalid UTF-8
        assert!(matches!(err(&[0x62, 0xff, 0xfe]), CborError::InvalidUtf8));
    }

    #[test]
    fn valid_utf8_accepted() {
        // 62 c3 a9 = "é" (2 bytes in UTF-8)
        assert_eq!(ok(&[0x62, 0xc3, 0xa9]), 3);
    }

    // ── Depth ──
    #[test]
    fn depth_32_ok() {
        // 32 nested arrays around null
        let mut bytes = vec![0x81; 32];
        bytes.push(0xf6);
        assert!(scan_top_level(&bytes).is_ok());
    }

    #[test]
    fn depth_33_rejected() {
        let mut bytes = vec![0x81; 33];
        bytes.push(0xf6);
        assert!(matches!(scan_top_level(&bytes), Err(CborError::Malformed { .. })));
    }

    // ── Stray break ──
    #[test]
    fn stray_break_rejected() {
        assert!(matches!(err(&[0xff]), CborError::Malformed { .. }));
    }
}

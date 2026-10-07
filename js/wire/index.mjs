// ADIE JavaScript wire adapter — public API (Phase 3, Gate 1, 3A.4A / D.7).
//
// Trust boundary:
//   cbor@9.0.2  = codec primitive  (byte-level CBOR codec)
//   rawcheck    = wire authority    (rejects non-DCP-2.1 wire forms)
//   profile     = semantic authority (validates decoded values)
//
// Public surface:
//   encode(AdieValue)          -> Buffer (canonical CBOR)
//   decode(Uint8Array)         -> AdieValue
//   rawcheck(Uint8Array)       -> {ok, consumed}   (wire gate)
//   profileValidate(any)       -> AdieValue        (semantic gate)
//   value constructors: uint, int, bytes, text, bool, nul, array, map
//   error classes:  all 14 E_WIRE_* codes

export { encode } from './encoder.mjs';
export { decode } from './decoder.mjs';
export { rawcheck } from './rawcheck.mjs';
export { validate as profileValidate } from './profile.mjs';

export {
  uint, int, bytes, text, bool, nul, array, map,
  encodeUintShortest, cmpUintRfc8949, canonicalizeMap,
  U64_MAX, I64_MIN, I64_MAX,
} from './value.mjs';

export {
  CborError, Malformed, Trailing, Indefinite, Float, Tag,
  DuplicateKey, NonCanonicalInt, NonCanonicalMap, InvalidUtf8,
  TypeMismatch, MissingField, UnknownCritical, Version, Ambiguous,
} from './error.mjs';

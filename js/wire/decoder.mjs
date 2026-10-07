// ADIE JavaScript decoder (Phase 3, Gate 1, 3A.4A / D.6).
//
// Pipeline: bytes → rawcheck → cbor@9 → profile → AdieValue
//           → canonical re-encode → byte-compare.
//
// Architectural invariant (DEFECT-026 / T32):
//   Profile validates semantic values.
//   Rawcheck validates information that semantic decoding may erase.
//
// The decoder MUST NOT bypass rawcheck. The re-encode comparison is
// the defense-in-depth check for map-key canonical ordering (which
// rawcheck intentionally leaves to the semantic layer).

import CBOR from 'cbor';
import { rawcheck } from './rawcheck.mjs';
import { validate as profileValidate } from './profile.mjs';
import { encode } from './encoder.mjs';
import { Malformed, NonCanonicalMap } from './error.mjs';

export function decode(bytes) {
  if (!(bytes instanceof Uint8Array)) {
    throw new TypeError('decode expects Uint8Array');
  }

  // 1. Wire-level authority (before cbor@9).
  rawcheck(bytes);

  // 2. Semantic decode (cbor@9).
  let jsValue;
  try {
    // DEFECT-028: force Map output for ALL CBOR maps (integer,
    // string, and empty). Mixed Map/object output would bypass the
    // profile's consistent-shape requirement.
    jsValue = CBOR.decodeFirstSync(Buffer.from(bytes), { preferMap: true });
  } catch (e) {
    throw new Malformed(`cbor decode failed: ${e.message}`);
  }

  // 3. Semantic validation → canonical AdieValue.
  const adieValue = profileValidate(jsValue);

  // 4. Canonical re-encode comparison. Catches unsorted map keys
  //    (which rawcheck deliberately does not inspect for ordering).
  let reEncoded;
  try {
    reEncoded = encode(adieValue);
  } catch (e) {
    throw new Malformed(`re-encode failed: ${e.message}`);
  }

  if (Buffer.compare(reEncoded, Buffer.from(bytes)) !== 0) {
    // Only canonical-map-order issues reach this point (rawcheck has
    // already rejected non-shortest integers, trailing, tags, etc.).
    throw new NonCanonicalMap();
  }

  return adieValue;
}

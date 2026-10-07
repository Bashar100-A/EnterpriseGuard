// ADIE CBOR profile validation (Phase 3, Gate 1, 3A.4A).
//
// Mirror of protocol/wire/profile.py and
// rust/adie-primitives/src/cbor/profile.rs.
//
// Authority for what cbor@9-decoded JS value is admissible as
// DCP 2.1 payload. Both encoder and decoder route through validate().

import * as CBOR from 'cbor';
import {
  Malformed, Float as FloatErr, NonCanonicalInt, Tag as TagErr,
  TypeMismatch,
} from './error.mjs';
import { canonicalizeMap } from './value.mjs';

export const MAX_DEPTH = 32;

const U64_MAX = 0xFFFFFFFFFFFFFFFFn;
const I64_MIN = -0x8000000000000000n;
const I64_MAX =  0x7FFFFFFFFFFFFFFFn;

// Detect cbor@9's Tagged and Simple classes without importing them
// directly (their class names could change; property checks are safer).
function isTagged(v) {
  return v && typeof v === 'object' &&
         v.constructor && v.constructor.name === 'Tagged';
}
function isSimple(v) {
  return v && typeof v === 'object' &&
         v.constructor && v.constructor.name === 'Simple';
}

export function validate(obj) {
  return validateDepth(obj, 0);
}

function validateDepth(obj, depth) {
  if (depth > MAX_DEPTH) {
    throw new Malformed(`max nesting depth ${MAX_DEPTH} exceeded`);
  }

  // Null
  if (obj === null) return { t: 'null' };

  // Bool (must come before number; JS bool is not number, but be explicit)
  if (typeof obj === 'boolean') return { t: 'bool', v: obj };

  // Number or BigInt
  if (typeof obj === 'number' || typeof obj === 'bigint') {
    return intToAdie(obj);
  }

  // String
  if (typeof obj === 'string') return { t: 'text', v: obj };

  // Bytes (Uint8Array or Buffer)
  if (obj instanceof Uint8Array) {
    return { t: 'bytes', v: Buffer.from(obj).toString('hex') };
  }

  // Array
  if (Array.isArray(obj)) {
    const items = obj.map(x => validateDepth(x, depth + 1));
    return { t: 'array', v: items };
  }

  // Map (cbor@9 decodes CBOR maps to JS Map)
  if (obj instanceof Map) {
    const entries = [];
    for (const [k, v] of obj.entries()) {
      // Key must be a non-negative integer within u64.
      if (typeof k === 'boolean') {
        throw new TypeMismatch('map key', 'unsigned integer');
      }
      if (typeof k !== 'number' && typeof k !== 'bigint') {
        throw new TypeMismatch('map key', 'unsigned integer');
      }
      const kn = (typeof k === 'bigint') ? k : BigInt(k);
      if (kn < 0n || kn > U64_MAX) {
        throw new TypeMismatch('map key', 'unsigned integer in u64 range');
      }
      entries.push([kn, validateDepth(v, depth + 1)]);
    }
    // canonicalizeMap rejects duplicates and sorts by RFC 8949.
    return { t: 'map', v: canonicalizeMap(entries) };
  }

  // Known tag-result types (defense-in-depth; rawcheck is authoritative).
  if (obj instanceof Date) {
    throw new TagErr(0);
  }
  if (isTagged(obj)) {
    throw new TagErr(obj.tag ?? 0);
  }
  if (isSimple(obj)) {
    throw new Malformed(`simple value ${obj.value ?? '?'} is not permitted`);
  }

  // Unrecognised type
  throw new Malformed(
    `unrecognised JS type ${obj?.constructor?.name ?? typeof obj} ` +
    `(possibly a tag result or unknown value)`
  );
}

function intToAdie(n) {
  // DEFECT-026: BigInt() is a coercion primitive, not a validator.
  // Explicit guards BEFORE any conversion. Never silently truncate.
  if (typeof n === 'number') {
    if (!Number.isInteger(n)) {
      // 1.5, Infinity, -Infinity, NaN — never silently coerce.
      throw new FloatErr();
    }
    if (!Number.isSafeInteger(n)) {
      // Integer outside ±2^53-1 must arrive as BigInt, not lossy Number.
      throw new NonCanonicalInt();
    }
  }
  const bn = (typeof n === 'bigint') ? n : BigInt(n);
  if (bn >= 0n && bn <= U64_MAX) return { t: 'uint', v: bn };
  if (bn >= I64_MIN && bn < 0n) return { t: 'int', v: bn };
  throw new NonCanonicalInt();
}

export { intToAdie };

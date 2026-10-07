// ADIE value model (Phase 3, Gate 1, 3A.4A).
//
// Mirror of protocol/wire/value.py and
// rust/adie-primitives/src/cbor/value.rs.
//
// Uses tagged plain objects instead of classes. This format matches
// the JSON protocol used by rust/adie-primitives/src/bin/adie-cbor.rs,
// so the JS↔Rust differential is direct.
//
// Tagged forms:
//   {t: "uint",  v: <int>}          (0 <= v <= 2^64 - 1)
//   {t: "int",   v: <int>}          (-2^63 <= v <= 2^63 - 1)
//   {t: "bytes", v: "<hex>"}
//   {t: "text",  v: "<utf-8 string>"}
//   {t: "bool",  v: <true|false>}
//   {t: "null"}
//   {t: "array", v: [AdieValue, ...]}
//   {t: "map",   v: [[k, AdieValue], ...]}   (k: uint, sorted)

import { DuplicateKey } from './error.mjs';

export const U64_MAX = 0xFFFFFFFFFFFFFFFFn;
export const I64_MIN = -0x8000000000000000n;
export const I64_MAX =  0x7FFFFFFFFFFFFFFFn;

// ─── constructors ──────────────────────────────────────────

export function uint(n) {
  if (typeof n === 'bigint') {
    if (n < 0n || n > U64_MAX) throw new RangeError(`uint out of range: ${n}`);
    return { t: 'uint', v: n };
  }
  if (!Number.isInteger(n) || n < 0) throw new RangeError(`uint out of range: ${n}`);
  if (n > Number.MAX_SAFE_INTEGER) {
    throw new RangeError(`uint exceeds safe integer; use BigInt: ${n}`);
  }
  return { t: 'uint', v: n };
}

export function int(n) {
  if (typeof n === 'bigint') {
    if (n < I64_MIN || n > I64_MAX) throw new RangeError(`int out of range: ${n}`);
    return { t: 'int', v: n };
  }
  if (!Number.isInteger(n)) throw new RangeError(`int not integer: ${n}`);
  if (n < Number.MIN_SAFE_INTEGER || n > Number.MAX_SAFE_INTEGER) {
    throw new RangeError(`int exceeds safe range; use BigInt: ${n}`);
  }
  return { t: 'int', v: n };
}

export function bytes(hexOrBytes) {
  if (typeof hexOrBytes === 'string') {
    return { t: 'bytes', v: hexOrBytes };
  }
  if (hexOrBytes instanceof Uint8Array) {
    return { t: 'bytes', v: Buffer.from(hexOrBytes).toString('hex') };
  }
  throw new TypeError('bytes expects hex string or Uint8Array');
}

export function text(s) {
  if (typeof s !== 'string') throw new TypeError('text expects string');
  return { t: 'text', v: s };
}

export function bool(b) {
  if (typeof b !== 'boolean') throw new TypeError('bool expects boolean');
  return { t: 'bool', v: b };
}

export function nul() { return { t: 'null' }; }

export function array(items) {
  if (!Array.isArray(items)) throw new TypeError('array expects array');
  return { t: 'array', v: [...items] };
}

export function map(entries) {
  if (!Array.isArray(entries)) throw new TypeError('map expects array');
  return { t: 'map', v: [...entries] };
}

// ─── encode_uint_shortest (mirror of Python/Rust) ──────────

export function encodeUintShortest(n) {
  const bn = (typeof n === 'bigint') ? n : BigInt(n);
  if (bn < 0n || bn > U64_MAX) throw new RangeError(`uint out of range: ${bn}`);
  if (bn < 24n) return Buffer.from([Number(bn)]);
  if (bn <= 0xFFn) return Buffer.from([0x18, Number(bn)]);
  if (bn <= 0xFFFFn) return Buffer.from([0x19, ...bufOfBE(bn, 2)]);
  if (bn <= 0xFFFFFFFFn) return Buffer.from([0x1A, ...bufOfBE(bn, 4)]);
  return Buffer.from([0x1B, ...bufOfBE(bn, 8)]);
}

function bufOfBE(bn, byteCount) {
  const out = new Uint8Array(byteCount);
  for (let i = byteCount - 1; i >= 0; i--) {
    out[i] = Number(bn & 0xFFn);
    bn >>= 8n;
  }
  return out;
}

// ─── cmp_uint_rfc8949 (RFC 8949 bytewise order) ────────────

export function cmpUintRfc8949(a, b) {
  const ea = encodeUintShortest(a);
  const eb = encodeUintShortest(b);
  return Buffer.compare(ea, eb);
}

// ─── canonicalize_map: sort + reject duplicates ───────────

export function canonicalizeMap(entries) {
  const sorted = [...entries].sort((x, y) => cmpUintRfc8949(x[0], y[0]));
  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1][0];
    const cur = sorted[i][0];
    const eq = (typeof prev === 'bigint' || typeof cur === 'bigint')
      ? BigInt(prev) === BigInt(cur)
      : prev === cur;
    if (eq) throw new DuplicateKey();
  }
  return sorted;
}

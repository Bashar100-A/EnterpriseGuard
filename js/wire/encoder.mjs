// ADIE JavaScript encoder (Phase 3, Gate 1, 3A.4A / D.5).
//
// AdieValue (tagged) → shape validation → cbor@9.0.2 encodeCanonical.
//
// Trust boundary:
//   cbor@9.0.2  = codec primitive
//   this module = protocol authority for AdieValue shapes
//
// Determinism: cbor@9.0.2 encodeCanonical produces shortest-form
// integers, sorted map keys (RFC 8949 §4.2.3), definite lengths only.

import CBOR from 'cbor';
import {
  Malformed, DuplicateKey, NonCanonicalInt,
} from './error.mjs';
import { canonicalizeMap, U64_MAX, I64_MIN, I64_MAX } from './value.mjs';

export const MAX_DEPTH = 32;

export function encode(value) {
  validateAdieValue(value, 0);
  const jsValue = toJsValue(value);
  return Buffer.from(CBOR.encodeCanonical(jsValue));
}

function validateAdieValue(node, depth) {
  if (depth > MAX_DEPTH) {
    throw new Malformed(`AdieValue depth ${depth} exceeds ${MAX_DEPTH}`);
  }
  if (node === null || typeof node !== 'object' || Array.isArray(node)) {
    throw new Malformed(`AdieValue node must be tagged object`);
  }
  const t = node.t;
  const v = node.v;
  switch (t) {
    case 'null':
      if (v !== undefined) throw new Malformed('null must not carry v');
      return;
    case 'bool':
      if (typeof v !== 'boolean') throw new Malformed('bool.v must be boolean');
      return;
    case 'uint':
      checkUint(v);
      return;
    case 'int':
      checkInt(v);
      return;
    case 'bytes':
      if (typeof v !== 'string') throw new Malformed('bytes.v must be hex string');
      if (v.length % 2 !== 0) throw new Malformed('bytes.v hex length must be even');
      if (!/^[0-9a-fA-F]*$/.test(v)) throw new Malformed('bytes.v must be hex');
      return;
    case 'text':
      if (typeof v !== 'string') throw new Malformed('text.v must be string');
      return;
    case 'array':
      if (!Array.isArray(v)) throw new Malformed('array.v must be array');
      for (const item of v) validateAdieValue(item, depth + 1);
      return;
    case 'map': {
      if (!Array.isArray(v)) throw new Malformed('map.v must be array of pairs');
      for (const pair of v) {
        if (!Array.isArray(pair) || pair.length !== 2) {
          throw new Malformed('map entry must be [k, value]');
        }
        checkUint(pair[0]);
        validateAdieValue(pair[1], depth + 1);
      }
      canonicalizeMap(v);  // throws DuplicateKey if duplicated
      return;
    }
    default:
      throw new Malformed(`unknown AdieValue tag ${JSON.stringify(t)}`);
  }
}

function checkUint(n) {
  if (typeof n === 'bigint') {
    if (n < 0n || n > U64_MAX) throw new NonCanonicalInt();
    return;
  }
  if (typeof n !== 'number' || !Number.isInteger(n) || n < 0) {
    throw new NonCanonicalInt();
  }
  if (!Number.isSafeInteger(n)) throw new NonCanonicalInt();
}

function checkInt(n) {
  if (typeof n === 'bigint') {
    if (n < I64_MIN || n > I64_MAX) throw new NonCanonicalInt();
    return;
  }
  if (typeof n !== 'number' || !Number.isInteger(n)) throw new NonCanonicalInt();
  if (!Number.isSafeInteger(n)) throw new NonCanonicalInt();
}

function toJsInt(bn) {
  const SAFE = BigInt(Number.MAX_SAFE_INTEGER);
  if (bn >= -SAFE && bn <= SAFE) return Number(bn);
  return bn;
}

function toJsValue(node) {
  switch (node.t) {
    case 'null':  return null;
    case 'bool':  return node.v;
    case 'uint':  return toJsInt(BigInt(node.v));
    case 'int':   return toJsInt(BigInt(node.v));
    case 'bytes': return Buffer.from(node.v, 'hex');
    case 'text':  return node.v;
    case 'array': return node.v.map(toJsValue);
    case 'map': {
      const sorted = canonicalizeMap(node.v);
      const m = new Map();
      for (const [k, val] of sorted) {
        m.set(toJsInt(BigInt(k)), toJsValue(val));
      }
      return m;
    }
  }
}

// ADIE JavaScript raw wire guard (Phase 3, Gate 1, 3A.4A / D.4).
//
// Mirror of protocol/wire/rawcheck.py and
// rust/adie-primitives/src/cbor/rawcheck.rs.
//
// Operates on the ORIGINAL CBOR bytes BEFORE cbor@9.0.2 runs.
// Its job: reject wire-level constructs whose semantic type would be
// erased by decoding.
//
// Responsibility boundary (DEFECT-026 / T32):
//   rawcheck validates wire-level invariants (structure, canonical
//   integer forms, no tags, no floats, no indefinite items).
//   profile validates semantic invariants (integer keys, sorted
//   keys, depth, types).
// The two MUST NOT duplicate each other's work.

import {
  Malformed, Trailing, Indefinite, Float as FloatErr, Tag as TagErr,
  NonCanonicalInt, InvalidUtf8, DuplicateKey,
} from './error.mjs';

export const MAX_DEPTH = 32;
const U32_MAX = 0xFFFFFFFFn;

export function rawcheck(bytes) {
  if (!(bytes instanceof Uint8Array)) {
    throw new TypeError('rawcheck expects Uint8Array');
  }
  const end = walkItem(bytes, 0, 0);
  if (end !== bytes.length) {
    throw new Trailing(bytes.length - end);
  }
  return { ok: true, consumed: end };
}

function walkItem(b, off, depth) {
  if (depth > MAX_DEPTH) {
    throw new Malformed(`depth ${depth} exceeds MAX_DEPTH=${MAX_DEPTH}`);
  }
  if (off >= b.length) throw new Malformed('truncated at head');
  const head = b[off];
  const mt = head >> 5;      // 0..7 always (major type)
  const ai = head & 0x1F;
  off += 1;

  switch (mt) {
    case 0:  // unsigned
    case 1:  // negative
      return walkInt(b, off, ai);
    case 2:
      return walkBytes(b, off, ai);
    case 3:
      return walkText(b, off, ai);
    case 4:
      return walkArray(b, off, ai, depth);
    case 5:
      return walkMap(b, off, ai, depth);
    case 6:
      return walkTag(b, off, ai);
    case 7:
      return walkSimple(b, off, ai);
  }
}

// Read additional value (definite). Rejects reserved AI + indefinite.
function readAdditional(b, off, ai) {
  if (ai < 24) return { value: BigInt(ai), off };
  if (ai === 24) {
    if (off + 1 > b.length) throw new Malformed('truncated ai24');
    return { value: BigInt(b[off]), off: off + 1 };
  }
  if (ai === 25) {
    if (off + 2 > b.length) throw new Malformed('truncated ai25');
    return {
      value: (BigInt(b[off]) << 8n) | BigInt(b[off + 1]),
      off: off + 2,
    };
  }
  if (ai === 26) {
    if (off + 4 > b.length) throw new Malformed('truncated ai26');
    let v = 0n;
    for (let i = 0; i < 4; i++) v = (v << 8n) | BigInt(b[off + i]);
    return { value: v, off: off + 4 };
  }
  if (ai === 27) {
    if (off + 8 > b.length) throw new Malformed('truncated ai27');
    let v = 0n;
    for (let i = 0; i < 8; i++) v = (v << 8n) | BigInt(b[off + i]);
    return { value: v, off: off + 8 };
  }
  if (ai === 28 || ai === 29 || ai === 30) {
    throw new Malformed(`reserved additional-info ${ai}`);
  }
  // ai === 31
  throw new Indefinite();
}

// Enforce shortest-form for the integer/arg value with given AI.
function checkShortest(v, ai) {
  if (v < 24n) {
    if (ai !== Number(v)) throw new NonCanonicalInt();
  } else if (v <= 0xFFn) {
    if (ai !== 24) throw new NonCanonicalInt();
  } else if (v <= 0xFFFFn) {
    if (ai !== 25) throw new NonCanonicalInt();
  } else if (v <= U32_MAX) {
    if (ai !== 26) throw new NonCanonicalInt();
  } else {
    if (ai !== 27) throw new NonCanonicalInt();
  }
}

function walkInt(b, off, ai) {
  const { value, off: next } = readAdditional(b, off, ai);
  checkShortest(value, ai);
  return next;
}

function walkBytes(b, off, ai) {
  const { value: len, off: next } = readAdditional(b, off, ai);
  checkShortest(len, ai);
  const n = Number(len);
  if (next + n > b.length) throw new Malformed('truncated bytes');
  return next + n;
}

const UTF8 = new TextDecoder('utf-8', { fatal: true });
function walkText(b, off, ai) {
  const { value: len, off: next } = readAdditional(b, off, ai);
  checkShortest(len, ai);
  const n = Number(len);
  if (next + n > b.length) throw new Malformed('truncated text');
  try { UTF8.decode(b.subarray(next, next + n)); }
  catch { throw new InvalidUtf8(); }
  return next + n;
}

function walkArray(b, off, ai, depth) {
  const { value: n, off: next } = readAdditional(b, off, ai);
  checkShortest(n, ai);
  let cur = next;
  for (let i = 0n; i < n; i++) {
    cur = walkItem(b, cur, depth + 1);
  }
  return cur;
}

function walkMap(b, off, ai, depth) {
  const { value: n, off: next } = readAdditional(b, off, ai);
  checkShortest(n, ai);
  let cur = next;
  // Duplicate-key detection at wire level (RFC 8949 §5.6).
  // cbor@9.0.2 decodes CBOR maps into JS Map objects, silently
  // deduplicating duplicate keys. Therefore rawcheck MUST reject
  // duplicates BEFORE cbor@9 runs. See DEFECT-027.
  const keyRanges = [];
  for (let i = 0n; i < n; i++) {
    const kStart = cur;
    cur = walkItem(b, cur, depth + 1);   // key
    const kEnd = cur;
    const kB = b.subarray(kStart, kEnd);
    for (const prev of keyRanges) {
      if (prev.length === kB.length) {
        let eq = true;
        for (let j = 0; j < kB.length; j++) {
          if (prev[j] !== kB[j]) { eq = false; break; }
        }
        if (eq) throw new DuplicateKey();
      }
    }
    keyRanges.push(kB);
    cur = walkItem(b, cur, depth + 1);   // value
  }
  return cur;
}

function walkTag(b, off, ai) {
  // Reject at the tag number level; do NOT walk the tagged value.
  const { value: tag } = readAdditional(b, off, ai);
  throw new TagErr(Number(tag));
}

function walkSimple(b, off, ai) {
  if (ai === 20) return off;                  // false
  if (ai === 21) return off;                  // true
  if (ai === 22) return off;                  // null
  if (ai === 23) throw new Malformed('undefined (0xf7) not permitted');
  if (ai === 24) {
    if (off + 1 > b.length) throw new Malformed('truncated simple24');
    const sb = b[off];
    if (sb < 32) throw new Malformed(`unassigned simple ${sb}`);
    throw new Malformed(`simple value ${sb} not permitted`);
  }
  if (ai === 25 || ai === 26 || ai === 27) throw new FloatErr();
  if (ai === 28 || ai === 29 || ai === 30) {
    throw new Malformed(`reserved simple additional-info ${ai}`);
  }
  // ai === 31 (0xff): break without indefinite context
  if (ai === 31) throw new Malformed('break without indefinite context');
  // ai 0..19: unassigned simple values
  throw new Malformed(`unassigned simple ${ai}`);
}

#!/usr/bin/env node
// ADIE wire decoder — JS conformance tests (D.6).

import { encode } from '../../../js/wire/encoder.mjs';
import { decode } from '../../../js/wire/decoder.mjs';
import {
  uint, int, bytes, text, bool, nul, array, map,
} from '../../../js/wire/value.mjs';
import {
  Malformed, Trailing, Indefinite, Float as FloatErr, Tag as TagErr,
  DuplicateKey, NonCanonicalInt, NonCanonicalMap, InvalidUtf8,
  TypeMismatch,
} from '../../../js/wire/error.mjs';

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}
function h2b(hex) { return Buffer.from(hex, 'hex'); }
function expectErr(fn, errType) {
  try { fn(); return false; } catch (e) { return e instanceof errType; }
}
function rtOk(name, v) {
  try {
    const bytes = encode(v);
    const back = decode(bytes);
    const re = encode(back);
    check(name, Buffer.compare(bytes, re) === 0, 'byte mismatch');
  } catch (e) {
    check(name, false, `${e.code || e.constructor.name}: ${e.message}`);
  }
}

console.log('='.repeat(72));
console.log('ADIE wire decoder — JS conformance');
console.log('='.repeat(72));

// ── Round-trip ──
rtOk('D01 rt null',              nul());
rtOk('D02 rt true',              bool(true));
rtOk('D03 rt false',             bool(false));
rtOk('D04 rt uint 0',            uint(0));
rtOk('D05 rt uint 24',           uint(24));
rtOk('D06 rt uint 256',          uint(256));
rtOk('D07 rt uint u32::MAX+1',   uint(0x100000000n));
rtOk('D08 rt uint u64::MAX',     uint(0xFFFFFFFFFFFFFFFFn));
rtOk('D09 rt int -1',            int(-1));
rtOk('D10 rt int -256',          int(-256));
rtOk('D11 rt text empty',        text(''));
rtOk('D12 rt text "hello"',      text('hello'));
rtOk('D13 rt bytes empty',       bytes(''));
rtOk('D14 rt bytes 010203',      bytes('010203'));
rtOk('D15 rt array empty',       array([]));
rtOk('D16 rt array [1,2,3]',     array([uint(1), uint(2), uint(3)]));
rtOk('D17 rt map empty',         map([]));
rtOk('D18 rt map {1:"a"}',       map([[1, text('a')]]));
rtOk('D19 rt map {1:"a",2:"b"}', map([[1, text('a')], [2, text('b')]]));
rtOk('D20 rt nested {1:[2,3]}',  map([[1, array([uint(2), uint(3)])]]));
rtOk('D21 rt complex',
     map([[1, text('v')], [2, array([uint(1), nul()])], [3, map([[256, bool(true)]])]]));

// ── rawcheck rejections (before cbor@9) ──
check('D22 reject tag',             expectErr(() => decode(h2b('c101')), TagErr));
check('D23 reject float16',         expectErr(() => decode(h2b('f93c00')), FloatErr));
check('D24 reject float32',         expectErr(() => decode(h2b('fa3f800000')), FloatErr));
check('D25 reject float64',         expectErr(() => decode(h2b('fb3ff0000000000000')), FloatErr));
check('D26 reject indefinite map',  expectErr(() => decode(h2b('bf016178ff')), Indefinite));
check('D27 reject indefinite arr',  expectErr(() => decode(h2b('9f01ff')), Indefinite));
check('D28 reject trailing',        expectErr(() => decode(h2b('00ff')), Trailing));
check('D29 reject non-shortest uint',   expectErr(() => decode(h2b('1801')), NonCanonicalInt));
check('D30 reject non-shortest bytes len', expectErr(() => decode(h2b('5800')), NonCanonicalInt));
check('D31 reject invalid UTF-8',   expectErr(() => decode(h2b('62fffe')), InvalidUtf8));
check('D32 reject undefined f7',    expectErr(() => decode(h2b('f7')), Malformed));
check('D33 reject break alone',     expectErr(() => decode(h2b('ff')), Malformed));

// ── Architectural boundary (rawcheck authority) ──
check('D34 ARCH uint "01" accepted',
      (() => { try { decode(h2b('01')); return true; } catch { return false; } })());
check('D35 ARCH float64 "fb3ff0000000000000" rejected',
      expectErr(() => decode(h2b('fb3ff0000000000000')), FloatErr));

// ── Duplicate keys (rawcheck detects at wire level) ──
check('D36 duplicate key rejected',
      expectErr(() => decode(h2b('a2016161016162')), DuplicateKey));

// ── Noncanonical map order (rawcheck accepts; re-encode check rejects) ──
// {2:"b",1:"a"} unsorted: a2 02 6162 01 6161
check('D37 unsorted map rejected',
      expectErr(() => decode(h2b('a2026162016161')), NonCanonicalMap));
// {1: {2:"b", 1:"a"}} nested unsorted: a1 01 a2 02 6162 01 6161
check('D38 nested unsorted map rejected',
      expectErr(() => decode(h2b('a101a2026162016161')), NonCanonicalMap));

// ── Semantic rejections by profile ──
// { "k": 1 } text key: a1 616b 01
check('D39 text key rejected',
      expectErr(() => decode(h2b('a1616b01')), TypeMismatch));
// { -1: 1 } negint key: a1 20 01
check('D40 negint key rejected',
      expectErr(() => decode(h2b('a12001')), TypeMismatch));

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));
process.exit(FAIL_N === 0 ? 0 : 1);

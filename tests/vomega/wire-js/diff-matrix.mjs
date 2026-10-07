#!/usr/bin/env node
// ADIE cross-implementation matrix (Stage 3A.4A-DIFF / D.8+D.9).
//
// For each vector class, probes Rust / Python / JavaScript with one
// representative input. Prints the resulting matrix: OK or E_WIRE_*.

import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import * as JS from '../../../js/wire/index.mjs';
import { stringify } from '../../../js/wire/bin/json-io.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT      = resolve(__dirname, '../../..');
const RUST_BIN  = resolve(ROOT, 'rust/adie-primitives/target/release/adie-cbor');
const PY_BIN    = resolve(ROOT, '.venv/bin/python');
const PY_SCRIPT = resolve(ROOT, 'protocol/wire/bin/adie-cbor.py');

function rustCall(p) {
  const r = spawnSync(RUST_BIN, [], { input: stringify(p), encoding:'utf8', timeout:20000 });
  try { return JSON.parse(r.stdout.trim()); } catch { return {error:'_PARSE'}; }
}
function pyCall(p) {
  const r = spawnSync(PY_BIN, [PY_SCRIPT], { input: stringify(p), encoding:'utf8', timeout:20000, cwd: ROOT });
  try { return JSON.parse(r.stdout.trim()); } catch { return {error:'_PARSE'}; }
}
function jsCall(p) {
  try {
    if (p.op === 'encode') {
      const b = JS.encode(p.value);
      return { cbor_hex: Buffer.from(b).toString('hex') };
    }
    if (p.op === 'decode') {
      const v = JS.decode(Buffer.from(p.cbor_hex, 'hex'));
      return { value: v };
    }
  } catch (e) { return { error: e.code || 'E_UNKNOWN' }; }
}

function verdict(r) {
  if (r.error) return r.error;
  if (r.cbor_hex !== undefined) return 'OK';
  if (r.value !== undefined) return 'OK';
  return '?';
}

const TABLE = [
  { cls: 'Valid encode',         op:'encode', value:{t:'uint',v:1} },
  { cls: 'Valid decode',         op:'decode', cbor_hex:'00' },
  { cls: 'Float rejection',      op:'decode', cbor_hex:'fb3ff0000000000000' },
  { cls: 'Tag rejection',        op:'decode', cbor_hex:'c101' },
  { cls: 'Duplicate keys',       op:'decode', cbor_hex:'a2016161016162' },
  { cls: 'Indefinite length',    op:'decode', cbor_hex:'9f01ff' },
  { cls: 'Trailing bytes',       op:'decode', cbor_hex:'00ff' },
  { cls: 'Non-shortest integer', op:'decode', cbor_hex:'1801' },
  { cls: 'Invalid UTF-8',        op:'decode', cbor_hex:'62fffe' },
  { cls: 'Invalid key type',     op:'decode', cbor_hex:'a1616b01' },
  { cls: 'Invalid value type',   op:'decode', cbor_hex:'a101f7' },
  { cls: 'Unknown critical',     op:'n/a',    cbor_hex:null },
];

console.log('='.repeat(84));
console.log('ADIE cross-implementation matrix: Rust | Python | JavaScript');
console.log('='.repeat(84));
console.log('CLASS                        | RUST              | PYTHON            | JAVASCRIPT');
console.log('-'.repeat(84));
for (const row of TABLE) {
  if (row.op === 'n/a') {
    console.log(`${row.cls.padEnd(28)} | N/A (semantic)    | N/A (semantic)    | N/A (semantic)`);
    continue;
  }
  const payload = row.op === 'encode'
    ? { op:'encode', value: row.value }
    : { op:'decode', cbor_hex: row.cbor_hex };
  const rs = verdict(rustCall(payload));
  const py = verdict(pyCall(payload));
  const js = verdict(jsCall(payload));
  console.log(`${row.cls.padEnd(28)} | ${rs.padEnd(17)} | ${py.padEnd(17)} | ${js}`);
}
console.log('='.repeat(84));

#!/usr/bin/env node
/**
 * JS KAT runner: @noble/post-quantum 0.7.1 vs NIST ACVP ML-DSA-65 (pure).
 * Located inside js/ so that @noble/post-quantum resolves.
 * Vectors loaded from ../tests/vomega/mldsa/kat/.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { ml_dsa65 } from '@noble/post-quantum/ml-dsa.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const KAT = join(HERE, '..', 'tests', 'vomega', 'mldsa', 'kat');

const load = (f) => JSON.parse(readFileSync(join(KAT, f), 'utf-8'));
const h2b = (h) => Buffer.from(h, 'hex');
const norm = (h) => (h || '').toUpperCase();

function runKeygen() {
  const vs = load('keygen_65.json');
  let p = 0, f = 0;
  for (const v of vs) {
    try {
      const kp = ml_dsa65.keygen(h2b(v.seed_hex));
      const pkOk = norm(Buffer.from(kp.publicKey).toString('hex')) === norm(v.pk_hex);
      const skOk = norm(Buffer.from(kp.secretKey).toString('hex')) === norm(v.sk_hex);
      if (pkOk && skOk) p++;
      else { f++; console.log(`  FAIL keygen tcId=${v.tcId} pk=${pkOk} sk=${skOk}`); }
    } catch (e) { f++; console.log(`  ERR  keygen tcId=${v.tcId}: ${e.message}`); }
  }
  console.log(`  keygen: ${p}/${p+f}`);
  return [p, f];
}

function runSiggen() {
  const vs = load('siggen_65.json');
  let p = 0, f = 0;
  for (const v of vs) {
    try {
      const ctx = v.context_hex ? h2b(v.context_hex) : new Uint8Array(0);
      const sig = ml_dsa65.sign(
        h2b(v.message_hex),
        h2b(v.sk_hex),
        { extraEntropy: false, context: ctx }
      );
      const got = norm(Buffer.from(sig).toString('hex'));
      if (got === norm(v.signature_hex)) p++;
      else { f++; console.log(`  FAIL siggen tcId=${v.tcId} got=${got.slice(0,32)} want=${v.signature_hex.slice(0,32)}`); }
    } catch (e) { f++; console.log(`  ERR  siggen tcId=${v.tcId}: ${e.message}`); }
  }
  console.log(`  siggen: ${p}/${p+f}`);
  return [p, f];
}

function runSigver() {
  const vs = load('sigver_65.json');
  let p = 0, f = 0;
  for (const v of vs) {
    try {
      const ctx = v.context_hex ? h2b(v.context_hex) : new Uint8Array(0);
      const ok = ml_dsa65.verify(
        h2b(v.signature_hex),
        h2b(v.message_hex),
        h2b(v.pk_hex),
        { context: ctx }
      );
      if (ok === v.testPassed) p++;
      else { f++; console.log(`  FAIL sigver tcId=${v.tcId} got=${ok} want=${v.testPassed}`); }
    } catch (e) { f++; console.log(`  ERR  sigver tcId=${v.tcId}: ${e.message}`); }
  }
  console.log(`  sigver: ${p}/${p+f}`);
  return [p, f];
}

console.log('=== JS KAT: @noble/post-quantum 0.7.1 vs NIST ACVP ML-DSA-65 (pure) ===');
const [k1, k2] = runKeygen();
const [g1, g2] = runSiggen();
const [v1, v2] = runSigver();
const totalP = k1 + g1 + v1;
const totalF = k2 + g2 + v2;
console.log();
console.log(`TOTAL: ${totalP}/${totalP + totalF}`);
process.exit(totalF === 0 ? 0 : 1);

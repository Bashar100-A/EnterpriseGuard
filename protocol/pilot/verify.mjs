#!/usr/bin/env node
/**
 * ADIE-PILOT v0.1 — JavaScript independent verifier (Phase 1.10).
 * Must produce byte-identical decision to protocol/pilot/verify_cli.py.
 *
 * Mirrors Python:
 *   - H_A domain-separated hashing
 *   - canonical JSON (sorted keys, no whitespace, UTF-8)
 *   - ClaimRoot with 14 fields (13 named + "proof-set" always ABSENT)
 *   - error message formats (str(VerifyError) = "{code}: {msg}"[:120])
 *     and special double-prefix slicing for BindingError
 */

import { createHash, createVerify } from 'node:crypto';
import { readFileSync } from 'node:fs';

// ─── H_A ────────────────────────────────────────────────────
const DOMAIN_PREFIX = Buffer.from('ADIE/vOmega/2/', 'utf-8');
function hA(t, x) {
  const tb = Buffer.from(t, 'utf-8');
  const lenBuf = Buffer.alloc(2);
  lenBuf.writeUInt16BE(tb.length, 0);
  return createHash('sha256')
    .update(DOMAIN_PREFIX).update(lenBuf).update(tb).update(x).digest();
}

// ─── canonical JSON ─────────────────────────────────────────
function canonicalBytes(x) {
  return Buffer.from(stableStringify(x), 'utf-8');
}
function stableStringify(x) {
  if (x === null) return 'null';
  if (typeof x === 'boolean') return x ? 'true' : 'false';
  if (typeof x === 'number') {
    if (!Number.isFinite(x)) throw new Error('non-finite');
    return JSON.stringify(x);
  }
  if (typeof x === 'string') return JSON.stringify(x);
  if (Array.isArray(x)) return '[' + x.map(stableStringify).join(',') + ']';
  if (typeof x === 'object') {
    const keys = Object.keys(x).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + stableStringify(x[k])).join(',') + '}';
  }
  throw new Error('unexpected type');
}

// ─── ClaimRoot ──────────────────────────────────────────────
const FIELD_NAMES_13 = [
  'issuer','subject','request','context','policy','model','data',
  'runtime','output','binding','temporal','evidence','authoring',
];
const FIELD_ORDER_14 = [...FIELD_NAMES_13, 'proof-set'];
const STATUS_ABSENT = 0x00, STATUS_PRESENT = 0x01, STATUS_NULL = 0x02;

function leaf(fid, status, canonical) {
  const idBuf = Buffer.alloc(2); idBuf.writeUInt16BE(fid, 0);
  const lenBuf = Buffer.alloc(4); lenBuf.writeUInt32BE(canonical.length, 0);
  const body = Buffer.concat([idBuf, Buffer.from([status]), lenBuf, canonical]);
  return hA('leaf', body);
}
function paddingLeaf() { return hA('padding', Buffer.alloc(0)); }
function parentNode(l, r) { return hA('node', Buffer.concat([l, r])); }

function computeClaimRoot(fields) {
  const leaves = [];
  for (let i = 0; i < FIELD_ORDER_14.length; i++) {
    const name = FIELD_ORDER_14[i];
    const fid = i + 1;
    if (!(name in fields)) {
      leaves.push(leaf(fid, STATUS_ABSENT, Buffer.alloc(0)));
      continue;
    }
    const v = fields[name];
    if (v === null || v === undefined) {
      leaves.push(leaf(fid, STATUS_NULL, Buffer.alloc(0)));
      continue;
    }
    leaves.push(leaf(fid, STATUS_PRESENT, canonicalBytes(v)));
  }
  let n = 1; while (n < leaves.length) n *= 2;
  const pad = paddingLeaf();
  while (leaves.length < n) leaves.push(pad);
  let level = leaves;
  while (level.length > 1) {
    const nxt = [];
    for (let i = 0; i < level.length; i += 2)
      nxt.push(parentNode(level[i], level[i + 1]));
    level = nxt;
  }
  return level[0];
}

// ─── ACL normalize (must match Python) ──────────────────────
function aclNormalize(e, depth = 0) {
  if (depth > 32) throw new Error('E208_NESTED_TOO_DEEP');
  if (!e || typeof e !== 'object' || !('op' in e)) return e;
  const op = e.op;
  if (op === 'NOT') {
    const i = aclNormalize(e.arg, depth + 1);
    if (i && typeof i === 'object' && i.op === 'NOT')
      return aclNormalize(i.arg, depth + 1);
    return { op: 'NOT', arg: i };
  }
  if (op === 'AND' || op === 'OR') {
    let flat = [];
    for (const a of e.args) {
      const n = aclNormalize(a, depth + 1);
      if (n && typeof n === 'object' && n.op === op) flat.push(...n.args);
      else flat.push(n);
    }
    if (op === 'AND') {
      if (flat.some(x => x && x.op === 'FALSE')) return { op: 'FALSE' };
      flat = flat.filter(x => !(x && x.op === 'TRUE'));
      if (flat.length === 0) return { op: 'TRUE' };
    } else {
      if (flat.some(x => x && x.op === 'TRUE')) return { op: 'TRUE' };
      flat = flat.filter(x => !(x && x.op === 'FALSE'));
      if (flat.length === 0) return { op: 'FALSE' };
    }
    if (flat.length === 1) return flat[0];
    flat.sort((a, b) => Buffer.compare(canonicalBytes(a), canonicalBytes(b)));
    return { op, args: flat };
  }
  return e;
}

// ─── emit ───────────────────────────────────────────────────
function emitValid(checks) {
  process.stdout.write(stableStringify({ status: 'VALID', checks }) + '\n');
  return 0;
}
function emitInvalid(code, message) {
  process.stdout.write(stableStringify({
    status: 'INVALID', code, message: message || ''
  }) + '\n');
  return 1;
}

// dcpMsg mirrors Python's str(VerifyError) = "{code}: {msg}" then [:120]
function dcpMsg(code, msg) {
  return `${code}: ${msg}`.slice(0, 120);
}
// bindingMsg mirrors Python's two-stage slicing for BindingError
function bindingMsg(code, rawMsg) {
  const sliced = `${code}: ${rawMsg}`.slice(0, 80);
  return `${code}: ${sliced}`.slice(0, 120);
}

// ─── constants ──────────────────────────────────────────────
const REQ = ['dcp_version','claim_id','issuer','subject','binding',
             'request','context','policy','model','data','runtime',
             'output','temporal','evidence','authoring',
             'proofs','claim_root','signature'];
const REQUIRED_AUTHORING_KEYS_SORTED = [
  'acl_version','canonical_ast_digest','compiler_digest',
  'meta_manifest_digest','parameter_digest','template_digest',
];
const ACL_VERSION = '0.1';

function isSha256(s) {
  return typeof s === 'string' && s.length === 71
      && s.startsWith('sha256:') && /^[0-9a-f]{64}$/.test(s.slice(7));
}

// ─── main ───────────────────────────────────────────────────
let input;
try { input = JSON.parse(readFileSync(0, 'utf-8')); }
catch (e) { process.exit(emitInvalid('E-INPUT', String(e).slice(0, 80))); }

const certText = input.certificate_json;
const pubPem = input.public_key_pem;
if (typeof certText !== 'string' || typeof pubPem !== 'string')
  process.exit(emitInvalid('E-INPUT', 'certificate_json/public_key_pem required'));

let cert;
try { cert = JSON.parse(certText); }
catch (e) { process.exit(emitInvalid('E-CANONICAL', String(e).slice(0, 80))); }

if (typeof cert !== 'object' || cert === null || Array.isArray(cert))
  process.exit(emitInvalid('E-SCHEMA', 'top-level must be object'));

for (const f of REQ) {
  if (!(f in cert))
    process.exit(emitInvalid('E-SCHEMA', dcpMsg('E-SCHEMA', 'missing ' + f)));
}
if (cert.dcp_version !== '2.0')
  process.exit(emitInvalid('E-VERSION',
    dcpMsg('E-VERSION', `dcp_version must be 2.0, got ${JSON.stringify(cert.dcp_version)}`)));

// ─── ClaimRoot ──────────────────────────────────────────────
const fields = {};
for (const k of FIELD_NAMES_13) {
  fields[k] = (cert[k] === undefined) ? null : cert[k];
}
const recomputed = 'sha256:' + computeClaimRoot(fields).toString('hex');
if (recomputed !== cert.claim_root) {
  const declared = String(cert.claim_root);
  process.exit(emitInvalid('E_CLAIM_ROOT_MISMATCH',
    dcpMsg('E_CLAIM_ROOT_MISMATCH',
      `declared ${declared.slice(0, 24)}, recomputed ${recomputed.slice(0, 24)}`)));
}

// ─── Binding ────────────────────────────────────────────────
const b = cert.binding;
if (!b || typeof b !== 'object')
  process.exit(emitInvalid('E-BINDING_MISSING_FIELD',
    dcpMsg('E-BINDING_MISSING_FIELD', 'binding')));

const reqH = 'sha256:' + hA('request', canonicalBytes(cert.request)).toString('hex');
if (b.request_hash !== reqH) {
  process.exit(emitInvalid('E-BINDING_REQUEST_HASH',
    dcpMsg('E-BINDING_REQUEST_HASH',
      `declared ${String(b.request_hash).slice(0, 20)}, recomputed ${reqH.slice(0, 20)}`)));
}
if (input.expected_audience !== undefined && b.audience !== input.expected_audience) {
  const rawMsg = `expected ${input.expected_audience}, got ${b.audience}`;
  process.exit(emitInvalid('E_BINDING_AUDIENCE_MISMATCH',
    bindingMsg('E_BINDING_AUDIENCE_MISMATCH', rawMsg)));
}

// ─── Signature ──────────────────────────────────────────────
if (!cert.signature || typeof cert.signature !== 'object')
  process.exit(emitInvalid('E_SIGNATURE',
    dcpMsg('E_SIGNATURE', 'signature must be object')));
if (cert.signature.alg !== 'RS256')
  process.exit(emitInvalid('E_SIGNATURE',
    dcpMsg('E_SIGNATURE', `unsupported alg ${JSON.stringify(cert.signature.alg)}`)));
if (typeof cert.signature.value !== 'string' || !cert.signature.value.startsWith('base64:'))
  process.exit(emitInvalid('E_SIGNATURE',
    dcpMsg('E_SIGNATURE', 'value must be base64:...')));

let sigBytes;
try {
  sigBytes = Buffer.from(cert.signature.value.slice(7), 'base64');
} catch (e) {
  process.exit(emitInvalid('E_SIGNATURE',
    dcpMsg('E_SIGNATURE', String(e).slice(0, 60))));
}
if (sigBytes.length === 0)
  process.exit(emitInvalid('E_SIGNATURE',
    dcpMsg('E_SIGNATURE', 'empty signature')));

const signed = {};
for (const k of Object.keys(cert)) if (k !== 'signature') signed[k] = cert[k];
const tbs = canonicalBytes(signed);

let verifyOk = false;
try {
  const v = createVerify('RSA-SHA256');
  v.update(tbs);
  verifyOk = v.verify(pubPem, sigBytes);
} catch (e) {
  process.exit(emitInvalid('E_SIGNATURE',
    dcpMsg('E_SIGNATURE', String(e).slice(0, 80))));
}
if (!verifyOk)
  // Match Python: pub.verify() raises InvalidSignature with str()==""
  // -> message = "E_SIGNATURE: "
  process.exit(emitInvalid('E_SIGNATURE', dcpMsg('E_SIGNATURE', '')));

// ─── Authoring closure ──────────────────────────────────────
const auth = cert.authoring;
if (!auth || typeof auth !== 'object')
  process.exit(emitInvalid('E-META-20', 'authoring missing'));
const authKeys = Object.keys(auth).sort();
if (JSON.stringify(authKeys) !== JSON.stringify(REQUIRED_AUTHORING_KEYS_SORTED))
  process.exit(emitInvalid('E-META-20', 'authoring keys mismatch'));
for (const k of ['template_digest','parameter_digest','compiler_digest',
                 'canonical_ast_digest','meta_manifest_digest']) {
  if (!isSha256(auth[k]))
    process.exit(emitInvalid('E-META-20', `${k} malformed`));
}
if (auth.acl_version !== ACL_VERSION)
  process.exit(emitInvalid('E-META-14', `authoring.acl_version != ${ACL_VERSION}`));

// ─── AST canonicalization ───────────────────────────────────
const pol = cert.policy;
if (!pol || typeof pol !== 'object')
  process.exit(emitInvalid('E-META-18', 'policy missing'));
const ast = pol.expression;
if (!ast || typeof ast !== 'object')
  process.exit(emitInvalid('E-META-18', 'policy.expression missing'));
const astDigest = 'sha256:' + hA('ast', canonicalBytes(aclNormalize(ast))).toString('hex');
if (astDigest !== auth.canonical_ast_digest)
  process.exit(emitInvalid('E-META-20', 'canonical_ast_digest mismatch'));

// ─── Optional manifest digest check ─────────────────────────
if (input.manifest && input.manifest.expected_digest) {
  if (input.manifest.expected_digest !== auth.meta_manifest_digest)
    process.exit(emitInvalid('E-META-20', 'manifest digest mismatch'));
}

process.exit(emitValid({
  acl_version: 'PASS',
  ast_canonicalization: 'PASS',
  authoring_closure: 'PASS',
  binding: 'PASS',
  claim_root: 'PASS',
  dcp20: 'PASS',
  signature: 'PASS',
}));

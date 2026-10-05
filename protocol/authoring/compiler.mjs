#!/usr/bin/env node
/**
 * ADIE-AUTHORING v0.1 — JavaScript independent compiler.
 * Must produce byte-identical closure to protocol/authoring/compiler.py.
 */

import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

// ─── constants ─────────────────────────────────────────────
const CODE_VERSION = 'AUTHORING-0.1';
const ACL_VERSION = '0.1';

const ALLOWED_OPS = new Set([
  'TRUE', 'FALSE', 'NOT', 'AND', 'OR',
  'EQ', 'NEQ', 'LT', 'LTE', 'GT', 'GTE', 'IN', 'EXISTS',
]);
const ALLOWED_TERMS = new Set(['FIELD', 'INT', 'STR', 'BOOL']);
const MAX_DEPTH = 32;

const REQUIRED_CLOSURE_KEYS = [
  'acl_version',
  'canonical_ast_digest',
  'compiler_digest',
  'meta_manifest_digest',
  'parameter_digest',
  'template_digest',
];

// ─── H_A ────────────────────────────────────────────────────
const DOMAIN_PREFIX = Buffer.from('ADIE/vOmega/2/', 'utf-8');

function hA(t, x) {
  const tb = Buffer.from(t, 'utf-8');
  if (tb.length > 0xFFFF) throw new Error('domain tag too long');
  const lenBuf = Buffer.alloc(2);
  lenBuf.writeUInt16BE(tb.length, 0);
  const sha = createHash('sha256');
  sha.update(DOMAIN_PREFIX);
  sha.update(lenBuf);
  sha.update(tb);
  sha.update(x);
  return sha.digest();
}

const CODE_DIGEST = 'sha256:' + hA(
  'compiler-code', Buffer.from(CODE_VERSION, 'utf-8')).toString('hex');

// ─── canonical JSON ─────────────────────────────────────────
function canonicalBytes(x) {
  return Buffer.from(stableStringify(x), 'utf-8');
}

function stableStringify(x) {
  if (x === null) return 'null';
  if (typeof x === 'boolean') return x ? 'true' : 'false';
  if (typeof x === 'number') {
    if (!Number.isFinite(x)) throw new Error('non-finite number');
    return JSON.stringify(x);
  }
  if (typeof x === 'string') return JSON.stringify(x);
  if (Array.isArray(x)) {
    return '[' + x.map(stableStringify).join(',') + ']';
  }
  if (typeof x === 'object') {
    const keys = Object.keys(x).sort();
    return '{' + keys.map(
      k => JSON.stringify(k) + ':' + stableStringify(x[k])
    ).join(',') + '}';
  }
  throw new Error('unexpected type ' + typeof x);
}

// ─── ACL validate ───────────────────────────────────────────
class ACLValidationError extends Error {
  constructor(code, msg = '') {
    super(`${code}: ${msg}`);
    this.code = code;
  }
}

function aclValidate(e, depth = 0) {
  if (depth > MAX_DEPTH) throw new ACLValidationError('E208_NESTED_TOO_DEEP', String(depth));
  if (!e || typeof e !== 'object' || Array.isArray(e) || !('op' in e)) {
    throw new ACLValidationError('E202_MALFORMED_AST', 'missing op');
  }
  const op = e.op;
  if (!ALLOWED_OPS.has(op)) throw new ACLValidationError('E201_UNKNOWN_OPERATOR', op);

  if (op === 'TRUE' || op === 'FALSE') return true;

  if (op === 'NOT') {
    if (!('arg' in e)) throw new ACLValidationError('E202_MALFORMED_AST', 'NOT missing arg');
    return aclValidate(e.arg, depth + 1);
  }

  if (op === 'AND' || op === 'OR') {
    const a = e.args;
    if (!Array.isArray(a) || a.length === 0) {
      throw new ACLValidationError(
        op === 'AND' ? 'E209_EMPTY_AND' : 'E210_EMPTY_OR', op);
    }
    for (const x of a) aclValidate(x, depth + 1);
    return true;
  }

  if (['EQ', 'NEQ', 'LT', 'LTE', 'GT', 'GTE'].includes(op)) {
    const a = e.args;
    if (!Array.isArray(a) || a.length !== 2) {
      throw new ACLValidationError('E202_MALFORMED_AST', `${op} needs 2 args`);
    }
    for (const x of a) aclValidateTerm(x);
    return true;
  }

  if (op === 'IN') {
    if (!('term' in e) || !('set' in e)) {
      throw new ACLValidationError('E202_MALFORMED_AST', 'IN missing term/set');
    }
    aclValidateTerm(e.term);
    if (!Array.isArray(e.set))
      throw new ACLValidationError('E202_MALFORMED_AST', 'IN.set not list');
    return true;
  }

  if (op === 'EXISTS') {
    if (typeof e.path !== 'string')
      throw new ACLValidationError('E202_MALFORMED_AST', 'EXISTS missing path');
    return true;
  }
  return true;
}

function aclValidateTerm(t) {
  if (!t || typeof t !== 'object' || Array.isArray(t) || !('t' in t)) {
    throw new ACLValidationError('E202_MALFORMED_AST', 'term missing t');
  }
  if (!ALLOWED_TERMS.has(t.t))
    throw new ACLValidationError('E202_MALFORMED_AST', `unknown term ${t.t}`);
  if (t.t === 'FIELD' && typeof t.path !== 'string')
    throw new ACLValidationError('E202_MALFORMED_AST', 'FIELD missing path');
  if (t.t === 'INT') {
    if (!Number.isInteger(t.v))
      throw new ACLValidationError('E211_NON_CANONICAL_INT', String(t.v));
  }
  return true;
}

// ─── ACL normalize (R01–R12) ────────────────────────────────
function aclNormalize(e, depth = 0) {
  if (depth > MAX_DEPTH) throw new ACLValidationError('E208_NESTED_TOO_DEEP', String(depth));
  if (!e || typeof e !== 'object' || !('op' in e)) return e;
  const op = e.op;

  if (op === 'NOT') {
    const inner = aclNormalize(e.arg, depth + 1);
    if (inner && typeof inner === 'object' && inner.op === 'NOT') {
      return aclNormalize(inner.arg, depth + 1);
    }
    return { op: 'NOT', arg: inner };
  }

  if (op === 'AND' || op === 'OR') {
    let flat = [];
    for (const a of e.args) {
      const n = aclNormalize(a, depth + 1);
      if (n && typeof n === 'object' && n.op === op) {
        flat.push(...n.args);
      } else {
        flat.push(n);
      }
    }
    if (op === 'AND') {
      if (flat.some(x => x && typeof x === 'object' && x.op === 'FALSE'))
        return { op: 'FALSE' };
      flat = flat.filter(x => !(x && typeof x === 'object' && x.op === 'TRUE'));
      if (flat.length === 0) return { op: 'TRUE' };
    } else {
      if (flat.some(x => x && typeof x === 'object' && x.op === 'TRUE'))
        return { op: 'TRUE' };
      flat = flat.filter(x => !(x && typeof x === 'object' && x.op === 'FALSE'));
      if (flat.length === 0) return { op: 'FALSE' };
    }
    if (flat.length === 1) return flat[0];
    flat.sort((a, b) => Buffer.compare(canonicalBytes(a), canonicalBytes(b)));
    return { op, args: flat };
  }

  return e;
}

// ─── Manifest computation ───────────────────────────────────
function universeSize(u) {
  return (u.acl_versions || []).length
       + (u.template_ids || []).length
       + (u.rewrite_ids || []).length
       + (u.registry_namespaces || []).length
       + (u.algorithms || []).length
       + (u.compat_relations || []).length;
}

function manifestDigest(m) {
  const body = {
    epoch: m.epoch,
    prev_epoch: m.prev_epoch,
    threshold: [m.threshold_k, m.threshold_n],
    universe_size: universeSize(m.universe),
  };
  return 'sha256:' + hA('manifest', canonicalBytes(body)).toString('hex');
}

// ─── AuthoringError ─────────────────────────────────────────
class AuthoringError extends Error {
  constructor(code, msg = '') {
    super(`${code}: ${msg}`);
    this.code = code;
  }
}

// ─── Compiler (frozen) ──────────────────────────────────────
class Compiler {
  constructor({ manifest, acl_version = ACL_VERSION } = {}) {
    if (!manifest || typeof manifest !== 'object') {
      throw new AuthoringError('E-META-20', 'manifest must be an object');
    }
    if (!manifest.digest) {
      manifest.digest = manifestDigest(manifest);
    }
    if (typeof manifest.digest !== 'string' || !manifest.digest) {
      throw new AuthoringError('E-META-20', 'manifest.digest is empty');
    }
    if (acl_version !== ACL_VERSION) {
      throw new AuthoringError('E-META-14',
        `unsupported acl_version ${JSON.stringify(acl_version)}; expected ${JSON.stringify(ACL_VERSION)}`);
    }
    this.manifest = manifest;
    this.acl_version = acl_version;
    Object.freeze(this);
  }

  get code_digest() { return CODE_DIGEST; }

  get identity() {
    const body = {
      code_digest: this.code_digest,
      manifest_digest: this.manifest.digest,
      acl_version: this.acl_version,
    };
    return 'sha256:' + hA('compiler-identity', canonicalBytes(body)).toString('hex');
  }

  compile(template, params) {
    if (!template || typeof template !== 'object' || Array.isArray(template)) {
      throw new AuthoringError('E-META-18', 'template must be an object');
    }

    const tid = template.template_id;
    if (typeof tid !== 'string' || !tid) {
      throw new AuthoringError('E-META-18', 'template_id missing or empty');
    }

    const tplAcl = template.acl_version;
    if (tplAcl !== this.acl_version) {
      throw new AuthoringError('E-META-14',
        `template.acl_version ${JSON.stringify(tplAcl)} != compiler ${JSON.stringify(this.acl_version)}`);
    }

    const declared = template.declared_params;
    if (!Array.isArray(declared)) {
      throw new AuthoringError('E-META-18', 'declared_params must be an array');
    }
    for (const x of declared) {
      if (typeof x !== 'string')
        throw new AuthoringError('E-META-18', 'declared_params entries must be strings');
    }
    const declaredSet = new Set(declared);

    const required = template.required_params || [];
    if (!Array.isArray(required)) {
      throw new AuthoringError('E-META-18', 'required_params must be an array');
    }
    for (const x of required) {
      if (typeof x !== 'string')
        throw new AuthoringError('E-META-18', 'required_params entries must be strings');
      if (!declaredSet.has(x)) {
        throw new AuthoringError('E-META-18',
          `required_params not subset of declared: ${JSON.stringify(x)}`);
      }
    }
    const requiredSet = new Set(required);

    if (template.purity !== 'PURE') {
      throw new AuthoringError('E-META-21',
        `purity must be PURE, got ${JSON.stringify(template.purity)}`);
    }

    if ('forbidden_env' in template && !Array.isArray(template.forbidden_env)) {
      throw new AuthoringError('E-META-18', 'forbidden_env must be an array');
    }

    if (!params || typeof params !== 'object' || Array.isArray(params)) {
      throw new AuthoringError('E-META-18', 'params must be an object');
    }
    for (const k of Object.keys(params)) {
      if (typeof k !== 'string')
        throw new AuthoringError('E-META-18', 'param keys must be strings');
      if (!declaredSet.has(k)) {
        throw new AuthoringError('E-META-18', `undeclared parameter ${JSON.stringify(k)}`);
      }
    }
    const missing = [...requiredSet].filter(k => !(k in params));
    if (missing.length) {
      throw new AuthoringError('E-META-18',
        `missing required params: ${JSON.stringify(missing)}`);
    }

    const ast = template.ast;
    if (!ast || typeof ast !== 'object' || Array.isArray(ast)) {
      throw new AuthoringError('E-META-18', 'ast missing or not an object');
    }
    try {
      aclValidate(ast);
    } catch (e) {
      if (e instanceof ACLValidationError) {
        throw new AuthoringError(e.code, e.message);
      }
      throw e;
    }

    const templateDigest = 'sha256:' + hA('template', canonicalBytes(template)).toString('hex');
    const parameterDigest = 'sha256:' + hA('parameters', canonicalBytes(params)).toString('hex');
    const normalizedAst = aclNormalize(ast);
    const canonicalAstDigest = 'sha256:' + hA('ast', canonicalBytes(normalizedAst)).toString('hex');

    const closure = {
      template_digest: templateDigest,
      parameter_digest: parameterDigest,
      compiler_digest: this.code_digest,
      acl_version: this.acl_version,
      canonical_ast_digest: canonicalAstDigest,
      meta_manifest_digest: this.manifest.digest,
    };

    const keys = Object.keys(closure).sort();
    if (JSON.stringify(keys) !== JSON.stringify(REQUIRED_CLOSURE_KEYS)) {
      throw new AuthoringError('E-META-20', 'closure keys mismatch');
    }
    for (const [k, v] of Object.entries(closure)) {
      if (typeof v !== 'string' || !v) {
        throw new AuthoringError('E-META-20', `closure field ${JSON.stringify(k)} empty`);
      }
    }
    return closure;
  }
}

// ─── CLI ────────────────────────────────────────────────────
function isMain() {
  try {
    const thisFile = fileURLToPath(import.meta.url);
    const mainFile = resolve(process.argv[1] || '');
    return thisFile === mainFile;
  } catch { return false; }
}

if (isMain()) {
  try {
    const input = JSON.parse(readFileSync(0, 'utf-8'));
    const c = new Compiler({
      manifest: input.manifest,
      acl_version: input.acl_version || ACL_VERSION,
    });
    const closure = c.compile(input.template, input.params);
    process.stdout.write(stableStringify(closure) + '\n');
  } catch (e) {
    const code = e.code || 'E-INTERNAL';
    process.stderr.write(`${code}\n`);
    process.exit(1);
  }
}

export { Compiler, AuthoringError, aclValidate, aclNormalize, hA, canonicalBytes };

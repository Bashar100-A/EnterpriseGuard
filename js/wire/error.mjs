// ADIE wire error codes (Phase 3, Gate 1, 3A.4A).
//
// Mirror of protocol/wire/error.py and
// rust/adie-primitives/src/cbor/error.rs.
//
// 14 codes, matching WIRE-FORMAT-0.2 §9 exactly.

export class CborError extends Error {
  constructor(message = '') {
    super(message);
    this.name = 'CborError';
    this.code = 'E_WIRE_UNKNOWN';
  }
  toString() { return this.code; }
}

export class Malformed extends CborError {
  constructor(detail = '') {
    super(detail);
    this.name = 'Malformed';
    this.code = 'E_WIRE_MALFORMED';
    this.detail = detail;
  }
  toString() { return this.detail ? `${this.code}: ${this.detail}` : this.code; }
}

export class Trailing extends CborError {
  constructor(extra) {
    super(`trailing ${extra}`);
    this.name = 'Trailing';
    this.code = 'E_WIRE_TRAILING';
    this.extra = extra;
  }
  toString() { return `${this.code}: ${this.extra} byte(s) after top-level item`; }
}

export class Indefinite extends CborError {
  constructor() {
    super();
    this.name = 'Indefinite';
    this.code = 'E_WIRE_INDEFINITE';
  }
}

export class Float_ extends CborError {
  constructor() {
    super();
    this.name = 'Float';
    this.code = 'E_WIRE_FLOAT';
  }
}
export { Float_ as Float };

export class Tag extends CborError {
  constructor(tag) {
    super(`tag ${tag}`);
    this.name = 'Tag';
    this.code = 'E_WIRE_TAG';
    this.tag = tag;
  }
  toString() { return `${this.code}: tag ${this.tag}`; }
}

export class DuplicateKey extends CborError {
  constructor() {
    super();
    this.name = 'DuplicateKey';
    this.code = 'E_WIRE_DUP_KEY';
  }
}

export class NonCanonicalInt extends CborError {
  constructor() {
    super();
    this.name = 'NonCanonicalInt';
    this.code = 'E_WIRE_NONCANONICAL_INT';
  }
}

export class NonCanonicalMap extends CborError {
  constructor() {
    super();
    this.name = 'NonCanonicalMap';
    this.code = 'E_WIRE_NONCANONICAL_MAP';
  }
}

export class InvalidUtf8 extends CborError {
  constructor() {
    super();
    this.name = 'InvalidUtf8';
    this.code = 'E_WIRE_INVALID_UTF8';
  }
}

export class TypeMismatch extends CborError {
  constructor(field, expected) {
    super(`field ${field} must be ${expected}`);
    this.name = 'TypeMismatch';
    this.code = 'E_WIRE_TYPE_MISMATCH';
    this.field = field;
    this.expected = expected;
  }
  toString() { return `${this.code}: field ${JSON.stringify(this.field)} must be ${this.expected}`; }
}

export class MissingField extends CborError {
  constructor(field) {
    super(`missing ${field}`);
    this.name = 'MissingField';
    this.code = 'E_WIRE_MISSING_FIELD';
    this.field = field;
  }
  toString() { return `${this.code}: missing field ${JSON.stringify(this.field)}`; }
}

export class UnknownCritical extends CborError {
  constructor(label) {
    super(`unknown critical label ${label}`);
    this.name = 'UnknownCritical';
    this.code = 'E_WIRE_UNKNOWN_CRITICAL';
    this.label = label;
  }
  toString() { return `${this.code}: unknown critical label ${this.label}`; }
}

export class Version extends CborError {
  constructor(got) {
    super(`version ${got}`);
    this.name = 'Version';
    this.code = 'E_WIRE_VERSION';
    this.got = got;
  }
  toString() { return `${this.code}: dcp_version must be "2.1", got ${JSON.stringify(this.got)}`; }
}

export class Ambiguous extends CborError {
  constructor(field) {
    super(`ambiguous ${field}`);
    this.name = 'Ambiguous';
    this.code = 'E_WIRE_AMBIGUOUS';
    this.field = field;
  }
  toString() { return `${this.code}: field ${JSON.stringify(this.field)} requires external state`; }
}

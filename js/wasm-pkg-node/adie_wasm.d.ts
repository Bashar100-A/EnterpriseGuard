/* tslint:disable */
/* eslint-disable */

/**
 * Decode canonical DCP 2.1 CBOR to an AdieValue (JSON string).
 * u64/i64 fields (values AND map keys) are returned as strings.
 * On error throws with an E_WIRE_* code.
 */
export function decode(bytes: Uint8Array): string;

/**
 * Encode an AdieValue (JSON string) to canonical DCP 2.1 CBOR.
 * Returns Uint8Array. On error throws with an E_WIRE_* or E_ABI/E_JSON code.
 */
export function encode(value_json: string): Uint8Array;

declare namespace wasm_bindgen {
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

}
declare type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

declare interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly decode: (a: number, b: number) => [number, number, number, number];
    readonly encode: (a: number, b: number) => [number, number, number, number];
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __externref_table_dealloc: (a: number) => void;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_start: () => void;
}

declare type SyncInitInput = BufferSource | WebAssembly.Module;

declare namespace wasm_bindgen {
    /**
     * Instantiates the given `module`, which can either be bytes or
     * a precompiled `WebAssembly.Module`.
     *
     * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
     *
     * @returns {InitOutput}
     */
    export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;
}

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
declare function wasm_bindgen (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;

/**
 * UI-01.J.2 — Shared contract primitives.
 *
 * Rules:
 *   - Optional fields are `T | null`, never `T | undefined`.
 *     JSON has no undefined; the wire format is always JSON.
 *   - Timestamps are ISO-8601 strings, branded to prevent accidental misuse.
 *   - Every list response carries a `requestId` for tracing.
 */

export type IsoDateTime = string & { readonly __brand: 'IsoDateTime' }

export interface PageRequest {
  cursor: string | null
  limit: number
}

export interface Page<T> {
  items: T[]
  nextCursor: string | null
  total: number
}

export interface DateRange {
  from: IsoDateTime | null
  to: IsoDateTime | null
}

export interface RequestMeta {
  requestId: string
}

export const DEFAULT_PAGE_LIMIT = 50 as const
export const MAX_PAGE_LIMIT = 200 as const

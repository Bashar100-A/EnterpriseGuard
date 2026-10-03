/**
 * UI-01.J.3 — Adapter layer primitives.
 *
 * Semantic rules (ADIE):
 *   - Adapters are the ONLY code that knows about HTTP endpoints.
 *   - Pages never see URLs; they call adapters.
 *   - When backend is absent, adapters throw NotConnectedError.
 *     They never fabricate data.
 */

import type { ApiClient } from '../api'

export type AdapterMode =
  | 'unavailable' // default — backend not wired
  | 'live'        // backend is real; calls hit the network
  | 'fixture'     // design fixtures only (docs playground); never in production pages

export interface AdapterContext {
  mode: AdapterMode
  client: ApiClient | null
}

export class NotConnectedError extends Error {
  readonly code = 'NOT_CONNECTED'
  readonly endpoint: string

  constructor(endpoint: string) {
    super(`Backend not connected: ${endpoint}`)
    this.name = 'NotConnectedError'
    this.endpoint = endpoint
  }
}

/**
 * Guard used by every adapter method.
 *
 * Narrows `ctx.client` to non-null in the returned scope, so callers
 * don't need `!` assertions.
 */
export function requireLiveClient(
  ctx: AdapterContext,
  endpoint: string,
): ApiClient {
  if (ctx.mode !== 'live' || ctx.client === null) {
    throw new NotConnectedError(endpoint)
  }
  return ctx.client
}

export const UNAVAILABLE_CONTEXT: AdapterContext = Object.freeze({
  mode: 'unavailable' as const,
  client: null,
})

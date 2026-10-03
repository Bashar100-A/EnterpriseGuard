/**
 * UI-01.J.1 — API contract types.
 *
 * Semantic rules (ADIE):
 *   - 'unknown' is a distinct kind, never merged into 'server' silently.
 *   - 'timeout' is separated from 'network' (user can distinguish).
 *   - 'auth' covers 401 + 403 (single actionable class for the UI).
 */

export type ApiErrorKind =
  | 'network'
  | 'timeout'
  | 'auth'
  | 'validation'
  | 'notFound'
  | 'server'
  | 'unknown'

export interface ApiError {
  kind: ApiErrorKind
  status: number | null
  message: string
  details?: unknown
  requestId?: string | null
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestConfig {
  method?: HttpMethod
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
  timeoutMs?: number
  query?: Record<string, string | number | boolean | undefined>
}

export interface ApiClientConfig {
  baseUrl: string
  defaultHeaders?: Record<string, string>
  defaultTimeoutMs?: number
  getAuthToken?: () => string | null
  fetchImpl?: typeof fetch
}

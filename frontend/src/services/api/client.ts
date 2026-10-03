/**
 * UI-01.J.1 — Unified HTTP client.
 *
 * Design constraints (see DEVELOPMENT.md):
 *   - No fabricated data. This module never returns mock payloads.
 *   - Errors are classified explicitly; 'unknown' is preserved as-is.
 *   - Uses the global fetch unless a fetchImpl is injected.
 *   - Timeout is enforced via AbortController, not Promise.race.
 *   - External AbortSignal is honored without confusing it with timeout.
 */

import type {
  ApiClientConfig,
  ApiError,
  ApiErrorKind,
  RequestConfig,
} from './types'

const DEFAULT_TIMEOUT_MS = 30_000

export class ApiClientError extends Error implements ApiError {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly details?: unknown
  readonly requestId?: string | null

  constructor(err: ApiError) {
    super(err.message)
    this.name = 'ApiClientError'
    this.kind = err.kind
    this.status = err.status
    this.details = err.details
    this.requestId = err.requestId ?? null
  }
}

function joinUrl(base: string, path: string): string {
  if (!base) return path
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const b = base.endsWith('/') ? base.slice(0, -1) : base
  const p = path.startsWith('/') ? path : `/${path}`
  return b + p
}

function buildQuery(query?: RequestConfig['query']): string {
  if (!query) return ''
  const parts: string[] = []
  for (const [k, v] of Object.entries(query)) {
    if (v === undefined) continue
    parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
  }
  return parts.length > 0 ? `?${parts.join('&')}` : ''
}

function mapStatus(status: number): ApiErrorKind {
  if (status === 401 || status === 403) return 'auth'
  if (status === 400 || status === 422) return 'validation'
  if (status === 404) return 'notFound'
  if (status >= 500) return 'server'
  return 'unknown'
}

function isAbortError(err: unknown): boolean {
  return (
    err instanceof Error &&
    (err.name === 'AbortError' || err.name === 'TimeoutError')
  )
}

export class ApiClient {
  private readonly config: ApiClientConfig

  constructor(config: ApiClientConfig) {
    if (!config || typeof config.baseUrl !== 'string') {
      throw new Error('ApiClient: baseUrl is required')
    }
    this.config = config
  }

  private resolveFetch(): typeof fetch {
    if (this.config.fetchImpl) return this.config.fetchImpl
    if (typeof fetch !== 'undefined') return fetch
    throw new Error('ApiClient: no fetch implementation available')
  }

  async request<T>(path: string, opts: RequestConfig = {}): Promise<T> {
    const method = opts.method ?? 'GET'
    const url = joinUrl(this.config.baseUrl, path) + buildQuery(opts.query)

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...this.config.defaultHeaders,
      ...opts.headers,
    }

    const token = this.config.getAuthToken?.() ?? null
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`
    }

    let body: string | undefined
    if (opts.body !== undefined && method !== 'GET') {
      if (typeof opts.body === 'string') {
        body = opts.body
      } else {
        body = JSON.stringify(opts.body)
        if (!headers['Content-Type']) {
          headers['Content-Type'] = 'application/json'
        }
      }
    }

    const timeoutMs =
      opts.timeoutMs ?? this.config.defaultTimeoutMs ?? DEFAULT_TIMEOUT_MS

    const controller = new AbortController()
    let timedOut = false
    const timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, timeoutMs)

    if (opts.signal) {
      if (opts.signal.aborted) {
        controller.abort()
      } else {
        opts.signal.addEventListener('abort', () => controller.abort(), {
          once: true,
        })
      }
    }

    const fetchImpl = this.resolveFetch()
    const init: RequestInit = {
      method,
      headers,
      signal: controller.signal,
    }
    if (body !== undefined) {
      init.body = body
    }
    let response: Response
    try {
      response = await fetchImpl(url, init)
    } catch (err) {
      if (isAbortError(err)) {
        if (timedOut) {
          throw new ApiClientError({
            kind: 'timeout',
            status: null,
            message: `Request timed out after ${timeoutMs}ms`,
            requestId: null,
          })
        }
        throw new ApiClientError({
          kind: 'network',
          status: null,
          message: 'Request aborted',
          requestId: null,
        })
      }
      throw new ApiClientError({
        kind: 'network',
        status: null,
        message: err instanceof Error ? err.message : 'Network error',
        requestId: null,
      })
    } finally {
      clearTimeout(timer)
    }

    const requestId = response.headers.get('x-request-id')

    if (!response.ok) {
      let details: unknown
      try {
        details = await response.json()
      } catch {
        details = undefined
      }
      throw new ApiClientError({
        kind: mapStatus(response.status),
        status: response.status,
        message: `HTTP ${response.status}`,
        details,
        requestId,
      })
    }

    if (response.status === 204) {
      return undefined as T
    }

    const contentType = response.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      return (await response.json()) as T
    }
    return (await response.text()) as unknown as T
  }

  get<T>(path: string, opts?: Omit<RequestConfig, 'method' | 'body'>): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'GET' })
  }

  post<T>(
    path: string,
    body?: unknown,
    opts?: Omit<RequestConfig, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'POST', body })
  }

  put<T>(
    path: string,
    body?: unknown,
    opts?: Omit<RequestConfig, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'PUT', body })
  }

  patch<T>(
    path: string,
    body?: unknown,
    opts?: Omit<RequestConfig, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'PATCH', body })
  }

  delete<T>(
    path: string,
    opts?: Omit<RequestConfig, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'DELETE' })
  }
}

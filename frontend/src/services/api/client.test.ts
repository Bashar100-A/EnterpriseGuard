import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiClient, ApiClientError } from './client'

function mockResponse(
  body: unknown,
  init: { status?: number; headers?: Record<string, string> } = {},
): Response {
  const status = init.status ?? 200
  const headers = new Headers(init.headers ?? {})
  if (!headers.has('content-type') && status !== 204) {
    headers.set('content-type', 'application/json')
  }
  return {
    ok: status >= 200 && status < 300,
    status,
    headers,
    async json() {
      return body
    },
    async text() {
      return typeof body === 'string' ? body : JSON.stringify(body)
    },
  } as unknown as Response
}

function abortError(): Error {
  const err = new Error('aborted')
  err.name = 'AbortError'
  return err
}

describe('ApiClient', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
  })

  it('throws when baseUrl is missing', () => {
    expect(
      () => new ApiClient({ baseUrl: undefined as unknown as string }),
    ).toThrow(/baseUrl is required/)
  })

  it('GET returns parsed JSON', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ ok: true }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    const data = await client.get<{ ok: boolean }>('/health')
    expect(data).toEqual({ ok: true })
  })

  it('joins baseUrl and path with leading slash', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.get('/health')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const url = fetchMock.mock.calls[0]![0]
    expect(url).toBe('https://x.test/health')
  })

  it('joins baseUrl and path without leading slash', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.get('health')
    expect(fetchMock.mock.calls[0]![0]).toBe('https://x.test/health')
  })

  it('does not double-slash when baseUrl ends with slash', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test/', fetchImpl: fetchMock })
    await client.get('/health')
    expect(fetchMock.mock.calls[0]![0]).toBe('https://x.test/health')
  })

  it('builds query string', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.get('/items', { query: { state: 'verified', limit: 10 } })
    const url = fetchMock.mock.calls[0]![0] as string
    expect(url).toContain('state=verified')
    expect(url).toContain('limit=10')
  })

  it('skips undefined query params', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.get('/items', { query: { a: undefined, b: 'x' } })
    const url = fetchMock.mock.calls[0]![0] as string
    expect(url).toContain('b=x')
    expect(url).not.toContain('a=')
  })

  it('encodes query keys and values', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.get('/items', { query: { 'a b': 'c d' } })
    expect(fetchMock.mock.calls[0]![0]).toContain('a%20b=c%20d')
  })

  it('attaches Authorization when token present', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({
      baseUrl: 'https://x.test',
      fetchImpl: fetchMock,
      getAuthToken: () => 'tok-123',
    })
    await client.get('/health')
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect((init.headers as Record<string, string>)['Authorization']).toBe(
      'Bearer tok-123',
    )
  })

  it('omits Authorization when no token', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({
      baseUrl: 'https://x.test',
      fetchImpl: fetchMock,
      getAuthToken: () => null,
    })
    await client.get('/health')
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect(
      (init.headers as Record<string, string>)['Authorization'],
    ).toBeUndefined()
  })

  it('does not override an explicit Authorization header', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({
      baseUrl: 'https://x.test',
      fetchImpl: fetchMock,
      getAuthToken: () => 'tok-123',
    })
    await client.get('/health', { headers: { Authorization: 'Custom xyz' } })
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect((init.headers as Record<string, string>)['Authorization']).toBe(
      'Custom xyz',
    )
  })

  it('merges defaultHeaders then request headers', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({
      baseUrl: 'https://x.test',
      fetchImpl: fetchMock,
      defaultHeaders: { 'X-App': 'eg', 'X-Tier': 'one' },
    })
    await client.get('/health', { headers: { 'X-Tier': 'two' } })
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(headers['X-App']).toBe('eg')
    expect(headers['X-Tier']).toBe('two')
  })

  it('POST serializes body and sets Content-Type', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.post('/items', { name: 'x' })
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect(init.body).toBe(JSON.stringify({ name: 'x' }))
    expect((init.headers as Record<string, string>)['Content-Type']).toBe(
      'application/json',
    )
  })

  it('POST with string body does not set Content-Type', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.post('/raw', 'plain text')
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect(init.body).toBe('plain text')
    expect(
      (init.headers as Record<string, string>)['Content-Type'],
    ).toBeUndefined()
  })

  it('GET does not send body even if provided', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.request('/health', { method: 'GET', body: { ignored: true } })
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect(init.body).toBeUndefined()
  })

  it('PUT / PATCH / DELETE helpers set the right method', async () => {
    fetchMock.mockResolvedValue(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.put('/a', {})
    await client.patch('/b', {})
    await client.delete('/c')
    expect((fetchMock.mock.calls[0]![1] as RequestInit).method).toBe('PUT')
    expect((fetchMock.mock.calls[1]![1] as RequestInit).method).toBe('PATCH')
    expect((fetchMock.mock.calls[2]![1] as RequestInit).method).toBe('DELETE')
  })

  it('204 returns undefined', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse(null, { status: 204 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    const r = await client.delete('/items/1')
    expect(r).toBeUndefined()
  })

  it('non-JSON response returns text', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse('plain text', {
        headers: { 'content-type': 'text/plain' },
      }),
    )
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    const r = await client.get<string>('/text')
    expect(r).toBe('plain text')
  })

  it('maps 401 to auth error', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 401 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({
      kind: 'auth',
      status: 401,
    })
  })

  it('maps 403 to auth error', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 403 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({ kind: 'auth' })
  })

  it('maps 400 to validation error', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 400 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({ kind: 'validation' })
  })

  it('maps 422 to validation error', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 422 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({ kind: 'validation' })
  })

  it('maps 404 to notFound', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 404 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({ kind: 'notFound' })
  })

  it('maps 500 / 503 to server error', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 500 }))
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 503 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/a')).rejects.toMatchObject({ kind: 'server' })
    await expect(client.get('/b')).rejects.toMatchObject({ kind: 'server' })
  })

  it('maps 418 to unknown kind', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, { status: 418 }))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({
      kind: 'unknown',
      status: 418,
    })
  })

  it('maps fetch rejection to network error', async () => {
    fetchMock.mockRejectedValueOnce(new Error('DNS fail'))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/x')).rejects.toMatchObject({ kind: 'network' })
  })

  it('maps abort (timeout) to timeout error', async () => {
    fetchMock.mockImplementationOnce(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          const sig = init.signal as AbortSignal | undefined
          if (!sig) return
          sig.addEventListener('abort', () => reject(abortError()), { once: true })
        }),
    )
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await expect(client.get('/slow', { timeoutMs: 15 })).rejects.toMatchObject({
      kind: 'timeout',
    })
  })

  it('maps external abort to network (not timeout)', async () => {
    fetchMock.mockImplementationOnce(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          const sig = init.signal as AbortSignal | undefined
          if (!sig) return
          sig.addEventListener('abort', () => reject(abortError()), { once: true })
        }),
    )
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    const ctrl = new AbortController()
    setTimeout(() => ctrl.abort(), 5)
    await expect(
      client.get('/x', { signal: ctrl.signal, timeoutMs: 5000 }),
    ).rejects.toMatchObject({ kind: 'network' })
  })

  it('extracts x-request-id from error responses', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({}, { status: 500, headers: { 'x-request-id': 'req-abc' } }),
    )
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    try {
      await client.get('/x')
      throw new Error('should have thrown')
    } catch (e) {
      expect(e).toBeInstanceOf(ApiClientError)
      expect((e as ApiClientError).requestId).toBe('req-abc')
    }
  })

  it('includes parsed details from JSON error body', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ code: 'E_BAD', field: 'name' }, { status: 400 }),
    )
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    try {
      await client.get('/x')
      throw new Error('should have thrown')
    } catch (e) {
      expect((e as ApiClientError).details).toEqual({ code: 'E_BAD', field: 'name' })
    }
  })

  it('uses the injected fetchImpl exactly once per call', async () => {
    fetchMock.mockResolvedValue(mockResponse({}))
    const client = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: fetchMock })
    await client.get('/a')
    await client.get('/b')
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiClient } from '../api'
import {
  createAdapters,
  createEvidenceAdapter,
  createDecisionAdapter,
  createManifestAdapter,
  createPolicyAdapter,
  createAuditAdapter,
  NotConnectedError,
  requireLiveClient,
  UNAVAILABLE_CONTEXT,
} from './index'
import type { AdapterContext } from './types'

function mockResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    async json() {
      return body
    },
    async text() {
      return JSON.stringify(body)
    },
  } as unknown as Response
}

function liveContext(fetchMock: ReturnType<typeof vi.fn>): AdapterContext {
  const client = new ApiClient({
    baseUrl: 'https://api.test',
    fetchImpl: fetchMock,
  })
  return { mode: 'live', client }
}

const emptyPage = { items: [], nextCursor: null, total: 0 }

describe('adapters — NotConnectedError', () => {
  it('has code NOT_CONNECTED', () => {
    const err = new NotConnectedError('evidence.list')
    expect(err.code).toBe('NOT_CONNECTED')
  })

  it('carries the endpoint name', () => {
    const err = new NotConnectedError('decision.detail')
    expect(err.endpoint).toBe('decision.detail')
  })

  it('has name NotConnectedError', () => {
    const err = new NotConnectedError('x')
    expect(err.name).toBe('NotConnectedError')
  })

  it('message includes the endpoint', () => {
    const err = new NotConnectedError('audit.list')
    expect(err.message).toContain('audit.list')
  })
})

describe('adapters — requireLiveClient', () => {
  it('throws in unavailable mode', () => {
    expect(() => requireLiveClient(UNAVAILABLE_CONTEXT, 'x')).toThrow(
      NotConnectedError,
    )
  })

  it('throws in fixture mode (J.6 will provide fixture path separately)', () => {
    expect(() =>
      requireLiveClient({ mode: 'fixture', client: null }, 'x'),
    ).toThrow(NotConnectedError)
  })

  it('throws when mode is live but client is null', () => {
    expect(() => requireLiveClient({ mode: 'live', client: null }, 'x')).toThrow(
      NotConnectedError,
    )
  })

  it('returns client in live mode', () => {
    const c = new ApiClient({ baseUrl: 'https://x.test', fetchImpl: vi.fn() })
    expect(requireLiveClient({ mode: 'live', client: c }, 'x')).toBe(c)
  })
})

describe('adapters — unavailable mode throws before any network call', () => {
  it('evidence.list throws', async () => {
    const a = createEvidenceAdapter(UNAVAILABLE_CONTEXT)
    await expect(
      a.list({ cursor: null, limit: 10, verification: null, source: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
  })

  it('decision.list throws', async () => {
    const a = createDecisionAdapter(UNAVAILABLE_CONTEXT)
    await expect(
      a.list({ cursor: null, limit: 10, state: null, impact: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
  })

  it('manifest.detail throws', async () => {
    const a = createManifestAdapter(UNAVAILABLE_CONTEXT)
    await expect(a.detail('m-1')).rejects.toBeInstanceOf(NotConnectedError)
  })

  it('policy.list throws', async () => {
    const a = createPolicyAdapter(UNAVAILABLE_CONTEXT)
    await expect(
      a.list({ cursor: null, limit: 10, state: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
  })

  it('audit.list throws', async () => {
    const a = createAuditAdapter(UNAVAILABLE_CONTEXT)
    await expect(
      a.list({ cursor: null, limit: 10, actorKind: null, outcome: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
  })
})

describe('adapters — live mode hits ApiClient with correct paths', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
  })

  it('evidence.list POSTs to /v1/evidence/list', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r', page: emptyPage }))
    const ctx = liveContext(fetchMock)
    await createEvidenceAdapter(ctx).list({
      cursor: null,
      limit: 10,
      verification: null,
      source: null,
    })
    const [url, init] = fetchMock.mock.calls[0]!
    expect(url).toBe('https://api.test/v1/evidence/list')
    expect((init as RequestInit).method).toBe('POST')
  })

  it('evidence.detail GETs /v1/evidence/:id', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r' }))
    const ctx = liveContext(fetchMock)
    await createEvidenceAdapter(ctx).detail('ev-42')
    const [url, init] = fetchMock.mock.calls[0]!
    expect(url).toBe('https://api.test/v1/evidence/ev-42')
    expect((init as RequestInit).method).toBe('GET')
  })

  it('evidence.detail encodes special chars in id', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}))
    const ctx = liveContext(fetchMock)
    await createEvidenceAdapter(ctx).detail('a/b c')
    const [url] = fetchMock.mock.calls[0]!
    expect(url).toBe('https://api.test/v1/evidence/a%2Fb%20c')
  })

  it('decision.list POSTs to /v1/decisions/list', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r', page: emptyPage }))
    const ctx = liveContext(fetchMock)
    await createDecisionAdapter(ctx).list({
      cursor: null,
      limit: 10,
      state: null,
      impact: null,
    })
    expect(fetchMock.mock.calls[0]![0]).toBe('https://api.test/v1/decisions/list')
  })

  it('manifest.list POSTs to /v1/manifests/list', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r', page: emptyPage }))
    const ctx = liveContext(fetchMock)
    await createManifestAdapter(ctx).list({
      cursor: null,
      limit: 10,
      state: null,
      decisionId: null,
    })
    expect(fetchMock.mock.calls[0]![0]).toBe('https://api.test/v1/manifests/list')
  })

  it('policy.list POSTs to /v1/policies/list', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r', page: emptyPage }))
    const ctx = liveContext(fetchMock)
    await createPolicyAdapter(ctx).list({ cursor: null, limit: 10, state: null })
    expect(fetchMock.mock.calls[0]![0]).toBe('https://api.test/v1/policies/list')
  })

  it('audit.list POSTs to /v1/audit/list', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r', page: emptyPage }))
    const ctx = liveContext(fetchMock)
    await createAuditAdapter(ctx).list({
      cursor: null,
      limit: 10,
      actorKind: null,
      outcome: null,
    })
    expect(fetchMock.mock.calls[0]![0]).toBe('https://api.test/v1/audit/list')
  })

  it('serializes request body as JSON', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ requestId: 'r', page: emptyPage }))
    const ctx = liveContext(fetchMock)
    const req = { cursor: null, limit: 25, verification: null, source: null } as const
    await createEvidenceAdapter(ctx).list(req)
    const init = fetchMock.mock.calls[0]![1] as RequestInit
    expect(JSON.parse(init.body as string)).toEqual(req)
  })
})

describe('adapters — createAdapters factory', () => {
  it('returns all five adapters', () => {
    const a = createAdapters(UNAVAILABLE_CONTEXT)
    expect(a.evidence).toBeDefined()
    expect(a.decision).toBeDefined()
    expect(a.manifest).toBeDefined()
    expect(a.policy).toBeDefined()
    expect(a.audit).toBeDefined()
  })

  it('UNAVAILABLE_CONTEXT is frozen', () => {
    expect(Object.isFrozen(UNAVAILABLE_CONTEXT)).toBe(true)
  })

  it('UNAVAILABLE_CONTEXT has mode unavailable', () => {
    expect(UNAVAILABLE_CONTEXT.mode).toBe('unavailable')
    expect(UNAVAILABLE_CONTEXT.client).toBeNull()
  })

  it('createAdapters in unavailable context throws on every adapter method', async () => {
    const a = createAdapters(UNAVAILABLE_CONTEXT)
    await expect(
      a.evidence.list({ cursor: null, limit: 10, verification: null, source: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
    await expect(
      a.decision.list({ cursor: null, limit: 10, state: null, impact: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
    await expect(
      a.manifest.list({ cursor: null, limit: 10, state: null, decisionId: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
    await expect(
      a.policy.list({ cursor: null, limit: 10, state: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
    await expect(
      a.audit.list({ cursor: null, limit: 10, actorKind: null, outcome: null }),
    ).rejects.toBeInstanceOf(NotConnectedError)
  })
})

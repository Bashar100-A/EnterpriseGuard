import { describe, it, expect } from 'vitest'
import { ApiClientError } from '../api'
import { NotConnectedError } from '../adapters'
import { classifyError } from './classify'

function apiErr(
  kind: 'network' | 'timeout' | 'auth' | 'validation' | 'notFound' | 'server' | 'unknown',
  status: number | null = null,
  requestId: string | null = null,
): ApiClientError {
  return new ApiClientError({
    kind,
    status,
    message: 'x',
    requestId,
  })
}

describe('errors — NotConnectedError', () => {
  it('classified as not-connected', () => {
    const c = classifyError(new NotConnectedError('evidence.list'))
    expect(c.kind).toBe('not-connected')
  })

  it('uses connection.notConnected key', () => {
    const c = classifyError(new NotConnectedError('x'))
    expect(c.key).toBe('connection.notConnected')
  })

  it('suggests connect-backend action', () => {
    const c = classifyError(new NotConnectedError('x'))
    expect(c.action).toBe('connect-backend')
  })

  it('preserves the raw error', () => {
    const e = new NotConnectedError('x')
    const c = classifyError(e)
    expect(c.raw).toBe(e)
  })

  it('has no status and no requestId', () => {
    const c = classifyError(new NotConnectedError('x'))
    expect(c.status).toBeNull()
    expect(c.requestId).toBeNull()
  })
})

describe('errors — ApiClientError kinds', () => {
  it('network → kind=network, action=retry', () => {
    const c = classifyError(apiErr('network'))
    expect(c.kind).toBe('network')
    expect(c.action).toBe('retry')
    expect(c.key).toBe('api.network')
  })

  it('timeout → kind=timeout, action=retry', () => {
    const c = classifyError(apiErr('timeout'))
    expect(c.kind).toBe('timeout')
    expect(c.action).toBe('retry')
    expect(c.key).toBe('api.timeout')
  })

  it('auth → action=reauthenticate', () => {
    const c = classifyError(apiErr('auth', 401))
    expect(c.kind).toBe('auth')
    expect(c.action).toBe('reauthenticate')
    expect(c.status).toBe(401)
  })

  it('validation → action=fix-input', () => {
    const c = classifyError(apiErr('validation', 400))
    expect(c.kind).toBe('validation')
    expect(c.action).toBe('fix-input')
  })

  it('notFound → action=navigate-back', () => {
    const c = classifyError(apiErr('notFound', 404))
    expect(c.kind).toBe('not-found')
    expect(c.action).toBe('navigate-back')
    expect(c.key).toBe('api.notFound')
  })

  it('server → action=wait-and-retry', () => {
    const c = classifyError(apiErr('server', 503))
    expect(c.kind).toBe('server')
    expect(c.action).toBe('wait-and-retry')
    expect(c.status).toBe(503)
  })

  it('unknown ApiClientError kind → kind=unknown', () => {
    const c = classifyError(apiErr('unknown', 418))
    expect(c.kind).toBe('unknown')
    expect(c.status).toBe(418)
  })

  it('preserves requestId', () => {
    const c = classifyError(apiErr('server', 500, 'req-xyz'))
    expect(c.requestId).toBe('req-xyz')
  })

  it('missing requestId becomes null', () => {
    const c = classifyError(apiErr('server', 500))
    expect(c.requestId).toBeNull()
  })
})

describe('errors — non-Api errors', () => {
  it('generic Error → unknown + contact-admin', () => {
    const c = classifyError(new Error('boom'))
    expect(c.kind).toBe('unknown')
    expect(c.action).toBe('contact-admin')
    expect(c.key).toBe('unknown.generic')
  })

  it('string throw → unknown', () => {
    const c = classifyError('nope')
    expect(c.kind).toBe('unknown')
    expect(c.raw).toBe('nope')
  })

  it('null → unknown', () => {
    const c = classifyError(null)
    expect(c.kind).toBe('unknown')
  })

  it('undefined → unknown', () => {
    const c = classifyError(undefined)
    expect(c.kind).toBe('unknown')
  })

  it('plain object → unknown', () => {
    const c = classifyError({ code: 'X' })
    expect(c.kind).toBe('unknown')
  })
})

describe('errors — invariants', () => {
  it('key is always a string', () => {
    const samples = [
      new NotConnectedError('x'),
      apiErr('network'),
      apiErr('auth', 401),
      new Error('x'),
      'raw',
      null,
    ]
    for (const s of samples) {
      expect(typeof classifyError(s).key).toBe('string')
      expect(classifyError(s).key.length).toBeGreaterThan(0)
    }
  })

  it('action is always a valid SuggestedAction', () => {
    const valid = new Set([
      'retry',
      'reauthenticate',
      'fix-input',
      'navigate-back',
      'wait-and-retry',
      'connect-backend',
      'contact-admin',
      'none',
    ])
    const samples = [
      new NotConnectedError('x'),
      apiErr('network'),
      apiErr('auth', 401),
      apiErr('validation', 400),
      apiErr('notFound', 404),
      apiErr('server', 500),
      new Error('x'),
    ]
    for (const s of samples) {
      expect(valid.has(classifyError(s).action)).toBe(true)
    }
  })

  it('is deterministic for the same input', () => {
    const e = apiErr('server', 500)
    const a = classifyError(e)
    const b = classifyError(e)
    expect(a.kind).toBe(b.kind)
    expect(a.key).toBe(b.key)
    expect(a.action).toBe(b.action)
  })

  it('NotConnectedError is NOT classified as network', () => {
    const c = classifyError(new NotConnectedError('x'))
    expect(c.kind).not.toBe('network')
    expect(c.kind).not.toBe('server')
  })

  it('unknown is preserved and never upgraded to server', () => {
    const c = classifyError(apiErr('unknown', 418))
    expect(c.kind).toBe('unknown')
    expect(c.kind).not.toBe('server')
  })
})

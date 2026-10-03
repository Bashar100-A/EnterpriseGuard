import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient } from '@tanstack/react-query'

import { createQueryClient } from './client'
import { queryKeys } from './keys'
import { AdapterProvider } from './AdapterProvider'
import { useAdapters } from './AdapterContext'
import { createAdapters, UNAVAILABLE_CONTEXT, NotConnectedError } from '../adapters'

describe('query — createQueryClient', () => {
  it('returns a QueryClient instance', () => {
    expect(createQueryClient()).toBeInstanceOf(QueryClient)
  })

  it('applies default staleTime of 30_000', () => {
    const c = createQueryClient()
    expect(c.getDefaultOptions().queries?.staleTime).toBe(30_000)
  })

  it('respects custom staleTime', () => {
    const c = createQueryClient({ staleTimeMs: 1000 })
    expect(c.getDefaultOptions().queries?.staleTime).toBe(1000)
  })

  it('applies gcTime of 5 minutes', () => {
    const c = createQueryClient()
    expect(c.getDefaultOptions().queries?.gcTime).toBe(5 * 60_000)
  })

  it('disables refetchOnWindowFocus', () => {
    const c = createQueryClient()
    expect(c.getDefaultOptions().queries?.refetchOnWindowFocus).toBe(false)
  })

  it('mutations do not retry', () => {
    const c = createQueryClient()
    expect(c.getDefaultOptions().mutations?.retry).toBe(false)
  })

  it('does not retry NotConnectedError', () => {
    const c = createQueryClient()
    const retry = c.getDefaultOptions().queries?.retry
    expect(typeof retry).toBe('function')
    if (typeof retry === 'function') {
      const result = retry(0, new NotConnectedError('x'))
      expect(result).toBe(false)
    }
  })

  it('retries generic errors up to maxRetries', () => {
    const c = createQueryClient({ maxRetries: 3 })
    const retry = c.getDefaultOptions().queries?.retry
    if (typeof retry === 'function') {
      const err = new Error('boom')
      expect(retry(0, err)).toBe(true)
      expect(retry(2, err)).toBe(true)
      expect(retry(3, err)).toBe(false)
    }
  })
})

describe('query — queryKeys', () => {
  it('evidence.all is a stable tuple', () => {
    expect(queryKeys.evidence.all).toEqual(['evidence'])
  })

  it('evidence.list includes the request', () => {
    const req = { cursor: null, limit: 10, verification: null, source: null } as const
    expect(queryKeys.evidence.list(req)).toEqual(['evidence', 'list', req])
  })

  it('evidence.detail includes the id', () => {
    expect(queryKeys.evidence.detail('ev-1')).toEqual(['evidence', 'detail', 'ev-1'])
  })

  it('decision.detail includes the id', () => {
    expect(queryKeys.decision.detail('d-9')).toEqual(['decision', 'detail', 'd-9'])
  })

  it('manifest.list includes the request', () => {
    const req = { cursor: null, limit: 5, state: null, decisionId: null } as const
    expect(queryKeys.manifest.list(req)).toEqual(['manifest', 'list', req])
  })

  it('policy.detail includes the id', () => {
    expect(queryKeys.policy.detail('p-1')).toEqual(['policy', 'detail', 'p-1'])
  })

  it('audit.list includes the request', () => {
    const req = { cursor: null, limit: 20, actorKind: null, outcome: null } as const
    expect(queryKeys.audit.list(req)).toEqual(['audit', 'list', req])
  })

  it('different domains produce different keys', () => {
    expect(queryKeys.evidence.all).not.toEqual(queryKeys.decision.all)
    expect(queryKeys.decision.all).not.toEqual(queryKeys.manifest.all)
  })

  it('keys are deterministic across calls', () => {
    expect(queryKeys.evidence.detail('x')).toEqual(queryKeys.evidence.detail('x'))
  })
})

describe('query — AdapterProvider + useAdapters', () => {
  function Consumer() {
    const adapters = useAdapters()
    const ok =
      adapters.evidence !== undefined &&
      adapters.decision !== undefined &&
      adapters.manifest !== undefined &&
      adapters.policy !== undefined &&
      adapters.audit !== undefined
    return <div data-testid="consumer">{ok ? 'ok' : 'missing'}</div>
  }

  it('provides adapters via useAdapters', () => {
    const adapters = createAdapters(UNAVAILABLE_CONTEXT)
    render(
      <AdapterProvider adapters={adapters}>
        <Consumer />
      </AdapterProvider>,
    )
    expect(screen.getByTestId('consumer').textContent).toBe('ok')
  })

  it('returns the exact same adapters instance', () => {
    const adapters = createAdapters(UNAVAILABLE_CONTEXT)
    let received: unknown = null
    function Capture() {
      received = useAdapters()
      return null
    }
    render(
      <AdapterProvider adapters={adapters}>
        <Capture />
      </AdapterProvider>,
    )
    expect(received).toBe(adapters)
  })

  it('useAdapters throws outside provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    try {
      expect(() => render(<Consumer />)).toThrow(
        /useAdapters must be used within <AdapterProvider>/,
      )
    } finally {
      spy.mockRestore()
    }
  })

  it('nested providers resolve to the innermost', () => {
    const outer = createAdapters(UNAVAILABLE_CONTEXT)
    const inner = createAdapters(UNAVAILABLE_CONTEXT)
    let received: unknown = null
    function Capture() {
      received = useAdapters()
      return null
    }
    render(
      <AdapterProvider adapters={outer}>
        <AdapterProvider adapters={inner}>
          <Capture />
        </AdapterProvider>
      </AdapterProvider>,
    )
    expect(received).toBe(inner)
  })
})

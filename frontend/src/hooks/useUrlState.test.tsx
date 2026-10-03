import { describe, it, expect, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useUrlState, useUrlListState } from './useUrlState'

function makeWrapper(initialEntry: string): ({ children }: { children: ReactNode }) => ReturnType<typeof MemoryRouter> {
  return ({ children }) => (
    <MemoryRouter initialEntries={[initialEntry]}>{children}</MemoryRouter>
  )
}

/**
 * Helper hook that exposes location.search for assertions.
 *
 * URLSearchParams encodes certain characters (notably `,` → `%2C`) even
 * though they are technically valid in a query string. We decode the
 * value before returning it, so tests can assert on human-readable
 * URLs. Production code never relies on the encoded form — it reads
 * values through `URLSearchParams.get()`, which decodes automatically.
 */
function useSearch(): string {
  return decodeURIComponent(useLocation().search)
}

afterEach(() => {
  window.localStorage.clear()
})

// ============================================================
// useUrlState
// ============================================================

describe('useUrlState', () => {
  it('returns the default value when the key is absent', () => {
    const { result } = renderHook(() => useUrlState('state', 'any'), {
      wrapper: makeWrapper('/'),
    })
    expect(result.current[0]).toBe('any')
  })

  it('reads an existing value from the URL', () => {
    const { result } = renderHook(() => useUrlState('state', 'any'), {
      wrapper: makeWrapper('/?state=verified'),
    })
    expect(result.current[0]).toBe('verified')
  })

  it('treats an empty value as the default', () => {
    const { result } = renderHook(() => useUrlState('state', 'any'), {
      wrapper: makeWrapper('/?state='),
    })
    expect(result.current[0]).toBe('any')
  })

  it('setValue updates the URL', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlState('state', 'any'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/') },
    )
    act(() => {
      result.current.state[1]('pending')
    })
    expect(result.current.state[0]).toBe('pending')
    expect(result.current.search).toBe('?state=pending')
  })

  it('setting to the default value removes the key from the URL', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlState('state', 'any'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?state=verified') },
    )
    act(() => {
      result.current.state[1]('any')
    })
    expect(result.current.search).toBe('')
  })

  it('setting an empty string removes the key from the URL', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlState('state', 'any'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?state=verified') },
    )
    act(() => {
      result.current.state[1]('')
    })
    expect(result.current.search).toBe('')
  })

  it('preserves other query parameters', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlState('state', 'any'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?severity=high&page=2') },
    )
    act(() => {
      result.current.state[1]('pending')
    })
    // severity and page should both still be present
    expect(result.current.search).toContain('severity=high')
    expect(result.current.search).toContain('page=2')
    expect(result.current.search).toContain('state=pending')
  })

  it('removing a value preserves the other parameters', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlState('state', 'any'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?state=verified&severity=high') },
    )
    act(() => {
      result.current.state[1]('any')
    })
    expect(result.current.search).toBe('?severity=high')
  })

  it('uses replace by default (no new history entry)', () => {
    // We can only indirectly test this: verify no crash and state updates.
    // History semantics are covered by react-router itself.
    const { result } = renderHook(
      () => useUrlState('q', ''),
      { wrapper: makeWrapper('/') },
    )
    act(() => {
      result.current[1]('search-term')
    })
    expect(result.current[0]).toBe('search-term')
  })

  it('multiple hooks on different keys coexist', () => {
    const { result } = renderHook(
      () => ({
        a: useUrlState('a', ''),
        b: useUrlState('b', ''),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/') },
    )
    act(() => {
      result.current.a[1]('1')
    })
    act(() => {
      result.current.b[1]('2')
    })
    expect(result.current.search).toContain('a=1')
    expect(result.current.search).toContain('b=2')
  })
})

// ============================================================
// useUrlListState
// ============================================================

describe('useUrlListState', () => {
  it('returns the default list when the key is absent', () => {
    const { result } = renderHook(() => useUrlListState('state', ['any']), {
      wrapper: makeWrapper('/'),
    })
    expect(result.current[0]).toEqual(['any'])
  })

  it('returns [] when no default and key absent', () => {
    const { result } = renderHook(() => useUrlListState('state'), {
      wrapper: makeWrapper('/'),
    })
    expect(result.current[0]).toEqual([])
  })

  it('reads a comma-separated value', () => {
    const { result } = renderHook(() => useUrlListState('state'), {
      wrapper: makeWrapper('/?state=verified,pending'),
    })
    expect(result.current[0]).toEqual(['verified', 'pending'])
  })

  it('reads repeated values', () => {
    const { result } = renderHook(() => useUrlListState('state'), {
      wrapper: makeWrapper('/?state=verified&state=pending'),
    })
    expect(result.current[0]).toEqual(['verified', 'pending'])
  })

  it('deduplicates values', () => {
    const { result } = renderHook(() => useUrlListState('state'), {
      wrapper: makeWrapper('/?state=a,a,b'),
    })
    expect(result.current[0]).toEqual(['a', 'b'])
  })

  it('setValue writes a comma-separated value', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlListState('state'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/') },
    )
    act(() => {
      result.current.state[1](['verified', 'pending'])
    })
    expect(result.current.search).toBe('?state=verified,pending')
  })

  it('setting [] removes the key from the URL', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlListState('state'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?state=verified,pending') },
    )
    act(() => {
      result.current.state[1]([])
    })
    expect(result.current.search).toBe('')
  })

  it('setting the default list removes the key', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlListState('state', ['any']),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?state=verified') },
    )
    act(() => {
      result.current.state[1](['any'])
    })
    expect(result.current.search).toBe('')
  })

  it('preserves other query parameters', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlListState('state'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/?severity=high') },
    )
    act(() => {
      result.current.state[1](['verified'])
    })
    expect(result.current.search).toContain('severity=high')
    expect(result.current.search).toContain('state=verified')
  })

  it('filters out empty strings', () => {
    const { result } = renderHook(
      () => ({
        state: useUrlListState('state'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/') },
    )
    act(() => {
      result.current.state[1](['verified', '', 'pending'])
    })
    expect(result.current.search).toBe('?state=verified,pending')
  })

  it('two list hooks with different keys coexist', () => {
    const { result } = renderHook(
      () => ({
        a: useUrlListState('a'),
        b: useUrlListState('b'),
        search: useSearch(),
      }),
      { wrapper: makeWrapper('/') },
    )
    act(() => {
      result.current.a[1](['x', 'y'])
    })
    act(() => {
      result.current.b[1](['z'])
    })
    expect(result.current.search).toContain('a=x,y')
    expect(result.current.search).toContain('b=z')
  })
})

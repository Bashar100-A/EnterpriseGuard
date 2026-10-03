import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

export interface UseUrlStateOptions {
  /**
   * When true (default), updating the URL uses `replace` semantics so
   * the browser history is not polluted with every change. When false,
   * every update creates a new history entry (useful when the value is
   * a deliberate navigation step).
   */
  replace?: boolean
}

/**
 * useUrlState — persist a single string value in the URL query string.
 *
 * Reads `?key=value` from the URL and returns the current value plus a
 * setter. When the value equals `defaultValue`, the key is removed from
 * the URL entirely — so URLs stay clean ("no filter" is not encoded as
 * an explicit "all=..." parameter).
 *
 * Requirements:
 *   - Must be used inside a Router (uses `useSearchParams`).
 *   - `defaultValue` should be stable across renders (module-level const
 *     or `useMemo`), otherwise the memoization won't kick in.
 *
 * Example:
 *   const [state, setState] = useUrlState('state', 'any')
 *   // ?state=verified  -> state === 'verified'
 *   // (no ?state)       -> state === 'any'
 *   setState('pending') // pushes ?state=pending  (with replace: false)
 *   setState('any')     // removes ?state
 */
export function useUrlState(
  key: string,
  defaultValue: string,
  options: UseUrlStateOptions = {},
): [string, (next: string) => void] {
  const { replace = true } = options
  const [searchParams, setSearchParams] = useSearchParams()

  const value = useMemo<string>(() => {
    const raw = searchParams.get(key)
    return raw === null || raw === '' ? defaultValue : raw
  }, [searchParams, key, defaultValue])

  const setValue = useCallback(
    (next: string) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev)
          if (next === defaultValue || next === '') {
            params.delete(key)
          } else {
            params.set(key, next)
          }
          return params
        },
        { replace },
      )
    },
    [key, defaultValue, replace, setSearchParams],
  )

  return [value, setValue]
}

/**
 * useUrlListState — persist a list of strings in a single query parameter.
 *
 * Stored compactly as a comma-separated value (`?state=verified,pending`).
 * On read, both comma-separated and repeated (`?state=a&state=b`) forms
 * are accepted, so external links built with either convention work.
 *
 * When the list equals `defaultValue` (order-sensitive) or is empty, the
 * parameter is removed from the URL.
 *
 * Example:
 *   const [states, setStates] = useUrlListState('state', [])
 *   setStates(['verified', 'pending'])  // ?state=verified,pending
 */
export function useUrlListState(
  key: string,
  defaultValue: readonly string[] = [],
  options: UseUrlStateOptions = {},
): [string[], (next: string[]) => void] {
  const { replace = true } = options
  const [searchParams, setSearchParams] = useSearchParams()

  // Default array identity is stable across renders.
  const stableDefault = useMemo(() => [...defaultValue], [defaultValue])

  const value = useMemo<string[]>(() => {
    const all = searchParams.getAll(key)
    if (all.length === 0) return stableDefault
    const flat: string[] = []
    for (const v of all) {
      for (const part of v.split(',')) {
        const trimmed = part.trim()
        if (trimmed.length > 0 && !flat.includes(trimmed)) {
          flat.push(trimmed)
        }
      }
    }
    return flat.length === 0 ? stableDefault : flat
  }, [searchParams, key, stableDefault])

  const setValue = useCallback(
    (next: string[]) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev)
          params.delete(key)
          const cleaned = next.filter((v) => v.length > 0)
          const sameAsDefault =
            cleaned.length === stableDefault.length &&
            cleaned.every((v, i) => v === stableDefault[i])
          if (cleaned.length > 0 && !sameAsDefault) {
            params.set(key, cleaned.join(','))
          }
          return params
        },
        { replace },
      )
    },
    [key, stableDefault, replace, setSearchParams],
  )

  return [value, setValue]
}

import { useEffect, useState } from 'react'

export const RAIL_STORAGE_KEY = 'eg.nav.expanded'

export function readInitialRailExpanded(): boolean {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(RAIL_STORAGE_KEY) === 'true'
}

/**
 * Keep the navigation rail's expanded state in sync with localStorage.
 * Persists across reloads; safe under SSR (defaults to collapsed).
 */
export function useRailExpanded(): [boolean, (next: boolean) => void] {
  const [expanded, setExpanded] = useState<boolean>(() => readInitialRailExpanded())

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(RAIL_STORAGE_KEY, expanded ? 'true' : 'false')
  }, [expanded])

  return [expanded, setExpanded]
}

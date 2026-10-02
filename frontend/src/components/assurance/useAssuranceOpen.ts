import { useEffect, useState } from 'react'

export const ASSURANCE_STORAGE_KEY = 'eg.assurance.open'

export function readInitialAssuranceOpen(): boolean {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(ASSURANCE_STORAGE_KEY) === 'true'
}

/**
 * Keep the assurance rail open/closed state in sync with localStorage.
 * Default: closed (matches spec — rail is contextual, not always visible).
 */
export function useAssuranceOpen(): [boolean, (next: boolean) => void] {
  const [open, setOpen] = useState<boolean>(() => readInitialAssuranceOpen())

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(ASSURANCE_STORAGE_KEY, open ? 'true' : 'false')
  }, [open])

  return [open, setOpen]
}

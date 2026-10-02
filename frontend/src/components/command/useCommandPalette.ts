import { useCallback, useEffect, useState } from 'react'

export interface UseCommandPaletteReturn {
  open: boolean
  setOpen: (next: boolean) => void
  toggle: () => void
}

/**
 * useCommandPalette — controls the palette's open state and binds
 * the global Ctrl+K / Cmd+K shortcut.
 *
 * The hook does NOT mount the palette; it only manages state.
 */
export function useCommandPalette(): UseCommandPaletteReturn {
  const [open, setOpen] = useState(false)

  const toggle = useCallback(() => setOpen((v) => !v), [])

  useEffect(() => {
    if (typeof window === 'undefined') return

    const onKeyDown = (e: KeyboardEvent): void => {
      const isK = e.key === 'k' || e.key === 'K'
      const hasModifier = e.ctrlKey || e.metaKey
      if (isK && hasModifier) {
        e.preventDefault()
        setOpen((v) => !v)
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [])

  return { open, setOpen, toggle }
}

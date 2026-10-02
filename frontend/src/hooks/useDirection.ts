import { useEffect, useState } from 'react'

export type Direction = 'ltr' | 'rtl'

/**
 * Read the current document direction from <html dir="...">.
 * Components use this to apply direction-aware behavior without
 * coupling to i18n. The source of truth remains the DOM attribute.
 */
export function getDocumentDirection(): Direction {
  if (typeof document === 'undefined') return 'ltr'
  return document.documentElement.dir === 'rtl' ? 'rtl' : 'ltr'
}

/**
 * Subscribe to changes of `document.documentElement.dir`.
 * Returns the current direction. Safe under SSR (defaults to 'ltr').
 */
export function useDirection(): Direction {
  const [dir, setDir] = useState<Direction>(() => getDocumentDirection())

  useEffect(() => {
    if (typeof document === 'undefined') return
    if (typeof MutationObserver !== 'function') return

    const observer = new MutationObserver(() => {
      setDir(getDocumentDirection())
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['dir'],
    })

    // Sync once in case direction changed between render and effect.
    setDir(getDocumentDirection())

    return () => {
      observer.disconnect()
    }
  }, [])

  return dir
}

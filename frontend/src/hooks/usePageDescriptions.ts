import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { PAGES } from '../search/pageIndex'

/**
 * usePageDescriptions — returns a map of route path → translated page
 * description. Loads all page namespaces at once via i18next's
 * multi-namespace `useTranslation` API.
 *
 * The returned record is memoized on the active language, so switching
 * language regenerates the descriptions and any consuming search index.
 */
export function usePageDescriptions(): Record<string, string> {
  const { t, i18n } = useTranslation(PAGES.map((p) => p.namespace))

  return useMemo(() => {
    const map: Record<string, string> = {}
    for (const p of PAGES) {
      const value = t('description', { ns: p.namespace })
      map[p.path] = typeof value === 'string' ? value : ''
    }
    return map
    // i18n.language is the real trigger for re-running
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t, i18n.language])
}

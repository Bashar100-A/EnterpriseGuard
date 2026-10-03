import { useEffect, useRef, useState, type ReactElement } from 'react'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { ROUTE_SPECS } from '../../app/router'

/**
 * RouteAnnouncer — announces page changes to assistive technology and keeps
 * document.title in sync with the current route.
 *
 * Behavior:
 *   - On every pathname change: updates document.title and pushes a polite
 *     announcement into a visually hidden live region.
 *   - On language change without path change: updates document.title only
 *     (re-announcing "Navigated to…" on language switch would be noise).
 *   - Unknown routes fall back to a generic "Page changed" message.
 *
 * Why a dedicated component:
 *   - WCAG 2.4.2 (Page Titled) and WCAG 4.1.3 (Status Messages).
 *   - Client-side routing bypasses the browser's native title/URL cues.
 *
 * Note on circular import:
 *   ROUTE_SPECS is imported from the router module. It is only accessed
 *   INSIDE useEffect — by the time the effect runs, all modules have been
 *   evaluated, so the live binding is initialized. Do not access
 *   ROUTE_SPECS at module top level here.
 */
export function RouteAnnouncer(): ReactElement {
  const location = useLocation()
  const { t, i18n } = useTranslation(['navigation', 'accessibility'])

  const lastPath = useRef<string | null>(null)
  const lastLang = useRef<string | null>(null)
  const [announcement, setAnnouncement] = useState<string>('')

  useEffect(() => {
    const path = location.pathname
    const lang = i18n.language

    const pathChanged = lastPath.current !== path
    const langChanged = lastLang.current !== lang

    if (!pathChanged && !langChanged) return

    lastPath.current = path
    lastLang.current = lang

    const spec = ROUTE_SPECS.find((s) => s.path === path)
    const titleKey = spec?.titleKey

    if (titleKey) {
      const pageTitle = String(t(`items.${titleKey}`, { ns: 'navigation' }))
      document.title = String(
        t('pageTitleTemplate', { ns: 'accessibility', title: pageTitle }),
      )
      if (pathChanged) {
        setAnnouncement(
          String(t('pageChanged', { ns: 'accessibility', title: pageTitle })),
        )
      }
    } else {
      document.title = String(t('appTitle', { ns: 'accessibility' }))
      if (pathChanged) {
        setAnnouncement(String(t('pageChangedFallback', { ns: 'accessibility' })))
      }
    }
  }, [location.pathname, t, i18n.language])

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="eg-visually-hidden"
      data-testid="route-announcer"
    >
      {announcement}
    </div>
  )
}

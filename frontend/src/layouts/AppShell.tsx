import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export interface AppShellProps {
  /** Optional top bar (rendered as <header role="banner">). */
  topbar?: ReactNode
  /** Optional navigation rail (rendered as <aside> on inline-start). */
  navigationRail?: ReactNode
  /** Optional assurance panel (rendered as <aside> on inline-end). */
  assuranceRail?: ReactNode
  /** Whether the assurance panel is visible. Defaults to false. */
  assuranceOpen?: boolean
  /** Main workspace content. */
  children: ReactNode
}

/**
 * AppShell — top-level application layout.
 *
 * Structure:
 *   ┌──────────────────────────────────────────┐
 *   │  topbar (optional)                       │
 *   ├────────┬─────────────────────────┬───────┤
 *   │  nav   │   workspace (children)  │ assur │
 *   └────────┴─────────────────────────┴───────┘
 *
 * No business logic. No data fetching. Pure layout.
 * Direction-aware (RTL/LTR) via CSS logical properties.
 */
export function AppShell({
  topbar,
  navigationRail,
  assuranceRail,
  assuranceOpen = false,
  children,
}: AppShellProps): ReactElement {
  const { t } = useTranslation('accessibility')

  const showTopbar = topbar !== undefined && topbar !== null
  const showNav = navigationRail !== undefined && navigationRail !== null
  const showAssurance = assuranceOpen && assuranceRail !== undefined && assuranceRail !== null

  return (
    <div className="eg-shell">
      <a href="#eg-main" className="eg-shell__skip-link">
        {t('skipToContent')}
      </a>

      {showTopbar && (
        <header className="eg-shell__topbar" role="banner">
          {topbar}
        </header>
      )}

      <div className="eg-shell__body">
        {showNav && (
          <aside className="eg-shell__nav" aria-label="Primary navigation">
            {navigationRail}
          </aside>
        )}

        <main className="eg-shell__workspace" id="eg-main" tabIndex={-1}>
          {children}
        </main>

        {showAssurance && (
          <aside className="eg-shell__assurance" aria-label="Assurance context">
            {assuranceRail}
          </aside>
        )}
      </div>
    </div>
  )
}

import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export type AssuranceState = 'verified' | 'unverified' | 'unknown' | 'critical'

export interface BreadcrumbItem {
  label: string
  /** Route target (informational during UI-01; no router wired yet). */
  to?: string
  /** Mark this item as the current page. */
  current?: boolean
}

export interface WorkspaceHeaderProps {
  breadcrumb?: BreadcrumbItem[]
  title: string
  description?: string
  /** Optional context strip or similar line (e.g., ContextStrip). */
  context?: ReactNode
  /** Optional action buttons (filter, export, etc.). */
  actions?: ReactNode
  /** Assurance state — rendered as a badge on the trailing side. */
  assuranceState?: AssuranceState
}

function AssuranceBadge({ state }: { state: AssuranceState }): ReactElement {
  const { t } = useTranslation('workspace')
  const label = t(`assurance.${state}`)
  return (
    <span
      className={`eg-workspace__assurance eg-workspace__assurance--${state}`}
      data-state={state}
      title={t('assurance.label')}
      aria-label={`${t('assurance.label')}: ${label}`}
    >
      {label}
    </span>
  )
}

/**
 * WorkspaceHeader — page-level header (spec §17).
 * Structure: breadcrumb / title + description / context strip / actions + assurance.
 * Pure layout. No business logic, no data fetching, no fake states.
 */
export function WorkspaceHeader({
  breadcrumb,
  title,
  description,
  context,
  actions,
  assuranceState,
}: WorkspaceHeaderProps): ReactElement {
  const hasBreadcrumb = breadcrumb !== undefined && breadcrumb.length > 0

  return (
    <header className="eg-workspace">
      {hasBreadcrumb && (
        <nav className="eg-workspace__breadcrumb" aria-label="Breadcrumb">
          <ol className="eg-workspace__breadcrumb-list">
            {breadcrumb.map((item, i) => (
              <li
                key={`${item.label}-${i}`}
                className="eg-workspace__breadcrumb-item"
              >
                {i > 0 && (
                  <span className="eg-workspace__breadcrumb-sep" aria-hidden="true">
                    /
                  </span>
                )}
                {item.current ? (
                  <span aria-current="page" className="eg-workspace__breadcrumb-current">
                    {item.label}
                  </span>
                ) : (
                  <span className="eg-workspace__breadcrumb-link">{item.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      <div className="eg-workspace__heading">
        <div className="eg-workspace__heading-text">
          <h1 className="eg-workspace__title">{title}</h1>
          {description !== undefined && description !== '' && (
            <p className="eg-workspace__description">{description}</p>
          )}
        </div>

        {(actions !== undefined || assuranceState !== undefined) && (
          <div className="eg-workspace__heading-side">
            {actions !== undefined && (
              <div className="eg-workspace__actions">{actions}</div>
            )}
            {assuranceState !== undefined && (
              <AssuranceBadge state={assuranceState} />
            )}
          </div>
        )}
      </div>

      {context !== undefined && (
        <div className="eg-workspace__context">{context}</div>
      )}
    </header>
  )
}

import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { WorkspaceHeader } from '../components/workspace'
import { ContextStrip } from '../components/workspace'

export interface PageShellProps {
  titleKey: string
  groupKey: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * PageShell — generic placeholder page for UI-01.
 * Renders a WorkspaceHeader (with honest assurance) + a not-connected note.
 * Replaced by real pages in later phases.
 */
export function PageShell({ titleKey, groupKey }: PageShellProps): ReactElement {
  const { t } = useTranslation('navigation')
  const { t: tW } = useTranslation('workspace')
  const { t: tE } = useTranslation('errors')

  const groupLabel = t(`groups.${groupKey}`)
  const pageTitle = t(`items.${titleKey}`)

  return (
    <>
      <WorkspaceHeader
        breadcrumb={[
          { label: tW('breadcrumb.home') },
          { label: groupLabel },
          { label: pageTitle, current: true },
        ]}
        title={pageTitle}
        description={tE('placeholder.foundationNote')}
        assuranceState="unknown"
        context={<ContextStrip environment={resolveEnvironment()} />}
      />
      <p className="eg-note">{tE('placeholder.notConnected')}</p>
    </>
  )
}

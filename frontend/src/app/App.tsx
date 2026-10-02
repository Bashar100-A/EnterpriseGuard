import { useState, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { AppShell } from '../layouts/AppShell'
import { NavigationRail, useRailExpanded } from '../components/navigation'
import { Topbar } from '../components/topbar'
import { ContextStrip, WorkspaceHeader } from '../components/workspace'
import type { NavigationItem } from '../components/navigation'

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

export default function App(): ReactElement {
  const [expanded, setExpanded] = useRailExpanded()
  const [activePath, setActivePath] = useState('/')
  const { t } = useTranslation('workspace')

  const handleNavigate = (item: NavigationItem): void => {
    setActivePath(item.to)
  }

  // Breadcrumb shows only the path prefix; the current page identity
  // is rendered as the h1 title below. This avoids duplicating the
  // page name in both places (and keeps getByText unambiguous).
  const breadcrumb = [{ label: t('breadcrumb.home'), current: true }]

  return (
    <AppShell
      topbar={<Topbar currentPath={activePath} />}
      navigationRail={
        <NavigationRail
          expanded={expanded}
          onToggleExpanded={() => setExpanded(!expanded)}
          activePath={activePath}
          onNavigate={handleNavigate}
        />
      }
    >
      <WorkspaceHeader
        breadcrumb={breadcrumb}
        title={t('foundation.title')}
        description={t('foundation.status')}
        assuranceState="unknown"
        context={<ContextStrip environment={resolveEnvironment()} />}
      />
      <p className="eg-note">{t('foundation.note')}</p>
    </AppShell>
  )
}

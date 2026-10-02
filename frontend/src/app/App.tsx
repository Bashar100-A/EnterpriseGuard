import { useState, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { AppShell } from '../layouts/AppShell'
import { NavigationRail, useRailExpanded } from '../components/navigation'
import { Topbar } from '../components/topbar'
import { AssuranceRail, useAssuranceOpen } from '../components/assurance'
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
  const [navExpanded, setNavExpanded] = useRailExpanded()
  const [assuranceOpen, setAssuranceOpen] = useAssuranceOpen()
  const [activePath, setActivePath] = useState('/')
  const { t } = useTranslation('workspace')

  const handleNavigate = (item: NavigationItem): void => {
    setActivePath(item.to)
  }

  const breadcrumb = [{ label: t('breadcrumb.home'), current: true }]

  return (
    <AppShell
      topbar={
        <Topbar
          currentPath={activePath}
          assuranceOpen={assuranceOpen}
          onToggleAssurance={() => setAssuranceOpen(!assuranceOpen)}
        />
      }
      navigationRail={
        <NavigationRail
          expanded={navExpanded}
          onToggleExpanded={() => setNavExpanded(!navExpanded)}
          activePath={activePath}
          onNavigate={handleNavigate}
        />
      }
      assuranceOpen={assuranceOpen}
      assuranceRail={<AssuranceRail onClose={() => setAssuranceOpen(false)} />}
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

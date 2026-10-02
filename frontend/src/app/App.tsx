import { useState, type ReactElement } from 'react'
import { AppShell } from '../layouts/AppShell'
import { NavigationRail, useRailExpanded } from '../components/navigation'
import { Topbar } from '../components/topbar'
import type { NavigationItem } from '../components/navigation'

/**
 * UI-01 foundation App — wires AppShell, NavigationRail, and Topbar.
 * Content is a placeholder while Phase C builds the rest of the layout.
 */
export default function App(): ReactElement {
  const [expanded, setExpanded] = useRailExpanded()
  const [activePath, setActivePath] = useState('/')

  const handleNavigate = (item: NavigationItem): void => {
    setActivePath(item.to)
  }

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
      <div>
        <h1 className="eg-title">Sovereign Control Surface</h1>
        <p className="eg-status">Foundation Ready — UI-01 Foundation</p>
        <p className="eg-note">Foundation environment — no operational data connected.</p>
      </div>
    </AppShell>
  )
}

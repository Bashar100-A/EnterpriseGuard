import type { ReactElement } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { AppShell } from '../layouts/AppShell'
import { NavigationRail, useRailExpanded } from '../components/navigation'
import { Topbar } from '../components/topbar'
import { AssuranceRail, useAssuranceOpen } from '../components/assurance'
import { CommandPalette, useCommandPalette } from '../components/command'
import { ShortcutsDialog } from '../components/shortcuts'
import { useCommands } from '../hooks/useCommands'
import { useGlobalShortcuts } from '../hooks/useGlobalShortcuts'
import type { NavigationItem } from '../components/navigation'

/**
 * RootLayout — the router-aware top-level component.
 *
 * Wires: AppShell, Topbar, NavigationRail, AssuranceRail,
 *        CommandPalette (Ctrl+K), ShortcutsDialog (?), global shortcuts.
 */
export function RootLayout(): ReactElement {
  const location = useLocation()
  const navigate = useNavigate()
  const [navExpanded, setNavExpanded] = useRailExpanded()
  const [assuranceOpen, setAssuranceOpen] = useAssuranceOpen()
  const { open: cmdOpen, setOpen: setCmdOpen } = useCommandPalette()

  const commands = useCommands({
    onToggleAssurance: () => setAssuranceOpen(!assuranceOpen),
    onToggleRail: () => setNavExpanded(!navExpanded),
  })

  const { helpOpen, closeHelp, entries } = useGlobalShortcuts({
    onToggleRail: () => setNavExpanded(!navExpanded),
    onToggleAssurance: () => setAssuranceOpen(!assuranceOpen),
  })

  const handleNavigate = (item: NavigationItem): void => {
    navigate(item.to)
  }

  return (
    <>
      <AppShell
        topbar={
          <Topbar
            currentPath={location.pathname}
            assuranceOpen={assuranceOpen}
            onToggleAssurance={() => setAssuranceOpen(!assuranceOpen)}
          />
        }
        navigationRail={
          <NavigationRail
            expanded={navExpanded}
            onToggleExpanded={() => setNavExpanded(!navExpanded)}
            activePath={location.pathname}
            onNavigate={handleNavigate}
          />
        }
        assuranceOpen={assuranceOpen}
        assuranceRail={<AssuranceRail onClose={() => setAssuranceOpen(false)} />}
      >
        <Outlet />
      </AppShell>

      <CommandPalette
        open={cmdOpen}
        onClose={() => setCmdOpen(false)}
        commands={commands}
      />

      <ShortcutsDialog
        open={helpOpen}
        onClose={closeHelp}
        shortcuts={entries}
      />
    </>
  )
}

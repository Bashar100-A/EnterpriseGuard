import type { ReactElement } from 'react'
import { AppShell } from '../layouts/AppShell'

/**
 * UI-01.B foundation App — placeholder content while Phase C builds
 * the actual layout components. The AppShell provides the top-level
 * structure; subsequent commits (C.2–C.6) fill the slots.
 */
export default function App(): ReactElement {
  return (
    <AppShell>
      <div>
        <h1 className="eg-title">Sovereign Control Surface</h1>
        <p className="eg-status">Foundation Ready — UI-01 Foundation</p>
        <p className="eg-note">Foundation environment — no operational data connected.</p>
      </div>
    </AppShell>
  )
}

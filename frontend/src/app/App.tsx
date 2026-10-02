import type { ReactElement } from 'react'

/**
 * UI-01.B.1 — Foundation-only App component.
 * No routing, no i18n, no API, no ADIE/SIBB logic, no operational data.
 */
export default function App(): ReactElement {
  return (
    <main className="eg-root" role="main">
      <h1 className="eg-title">Sovereign Control Surface</h1>
      <p className="eg-status">Foundation Ready — UI-01 Foundation</p>
      <p className="eg-note">
        Foundation environment — no operational data connected.
      </p>
    </main>
  )
}

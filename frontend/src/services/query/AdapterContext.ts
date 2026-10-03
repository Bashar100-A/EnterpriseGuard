/**
 * UI-01.J.4 — Adapter React context + hook.
 *
 * The context is defined in a .ts file (no JSX) so that AdapterProvider.tsx
 * can remain a pure component module (react-refresh rule).
 */

import { createContext, useContext } from 'react'
import type { Adapters } from '../adapters'

export const AdapterContext = createContext<Adapters | null>(null)

export function useAdapters(): Adapters {
  const ctx = useContext(AdapterContext)
  if (ctx === null) {
    throw new Error('useAdapters must be used within <AdapterProvider>')
  }
  return ctx
}

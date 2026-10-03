/**
 * UI-01.J.4 — AdapterProvider component.
 *
 * Wraps the app (or a subtree) with a concrete Adapters instance.
 * Kept intentionally free of side effects.
 */

import type { ReactNode } from 'react'
import { AdapterContext } from './AdapterContext'
import type { Adapters } from '../adapters'

export interface AdapterProviderProps {
  adapters: Adapters
  children: ReactNode
}

export function AdapterProvider({ adapters, children }: AdapterProviderProps) {
  return (
    <AdapterContext.Provider value={adapters}>
      {children}
    </AdapterContext.Provider>
  )
}

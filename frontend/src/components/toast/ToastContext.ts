import { createContext } from 'react'
import type { ToastContextValue } from './types'

/**
 * The toast context. Kept in a separate module so that both the
 * provider and the `useToast` hook can import it without triggering
 * the "react-refresh only-export-components" ESLint rule.
 */
export const ToastContext = createContext<ToastContextValue | null>(null)

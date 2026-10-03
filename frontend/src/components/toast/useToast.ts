import { useContext } from 'react'
import { ToastContext } from './ToastContext'
import type { ToastContextValue } from './types'

/**
 * useToast — access the toast API from any component inside a
 * `<ToastProvider>`. Throws a clear error when used outside.
 *
 * Example:
 *   const toast = useToast()
 *   toast.success('Policy created', { action: { label: 'View', onClick: ... } })
 */
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (ctx === null) {
    throw new Error('useToast must be used inside <ToastProvider>')
  }
  return ctx
}

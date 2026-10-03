import type { ReactNode } from 'react'

export type ToastType = 'info' | 'success' | 'warning' | 'error'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface ToastOptions {
  /** Semantic type. Default: 'info'. */
  type?: ToastType
  /** Primary message (required). */
  message: ReactNode
  /** Optional detailed description shown below the message. */
  description?: ReactNode
  /**
   * Auto-dismiss timeout in milliseconds. `0` disables auto-dismiss.
   * Defaults: info/success = 4000, warning = 6000, error = 8000.
   */
  duration?: number
  /** Optional action button (e.g., Undo, View, Retry). */
  action?: ToastAction
  /** When true, shows a dismiss button. Default: true. */
  dismissible?: boolean
}

export interface Toast extends Required<Pick<ToastOptions, 'type' | 'message' | 'duration' | 'dismissible'>> {
  id: string
  description?: ReactNode
  action?: ToastAction
  createdAt: number
}

export interface ToastContextValue {
  /** Push a toast. Returns its id. */
  show: (options: ToastOptions) => string
  /** Convenience helpers. */
  info: (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) => string
  success: (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) => string
  warning: (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) => string
  error: (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) => string
  /** Dismiss a specific toast. */
  dismiss: (id: string) => void
  /** Dismiss all toasts. */
  dismissAll: () => void
}

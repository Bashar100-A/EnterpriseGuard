import { useCallback, useMemo, useState, type ReactElement, type ReactNode } from 'react'
import { ToastContext } from './ToastContext'
import type { Toast, ToastContextValue, ToastOptions, ToastType } from './types'

const DEFAULT_DURATIONS: Record<ToastType, number> = {
  info: 4000,
  success: 4000,
  warning: 6000,
  error: 8000,
}

let toastCounter = 0

function nextId(): string {
  toastCounter += 1
  return `toast-${Date.now()}-${toastCounter}`
}

export interface ToastProviderProps {
  children: ReactNode
}

/**
 * ToastProvider — supplies the toast API to the app.
 *
 * The provider holds the toast list in state and exposes a stable
 * context value. Auto-dismiss is implemented by the individual
 * `<Toast>` components via `setTimeout` on mount, so the provider
 * itself remains synchronous and easy to test.
 */
export function ToastProvider({ children }: ToastProviderProps): ReactElement {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const dismissAll = useCallback(() => {
    setToasts([])
  }, [])

  const show = useCallback((options: ToastOptions): string => {
    const type = options.type ?? 'info'
    const duration = options.duration ?? DEFAULT_DURATIONS[type]
    const dismissible = options.dismissible ?? true
    const id = nextId()
    const toast: Toast = {
      id,
      type,
      message: options.message,
      duration,
      dismissible,
      createdAt: Date.now(),
    }
    if (options.description !== undefined) toast.description = options.description
    if (options.action !== undefined) toast.action = options.action
    setToasts((prev) => [...prev, toast])
    return id
  }, [])

  const info = useCallback(
    (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) =>
      show({ ...options, message, type: 'info' }),
    [show],
  )
  const success = useCallback(
    (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) =>
      show({ ...options, message, type: 'success' }),
    [show],
  )
  const warning = useCallback(
    (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) =>
      show({ ...options, message, type: 'warning' }),
    [show],
  )
  const error = useCallback(
    (message: ReactNode, options?: Omit<ToastOptions, 'message' | 'type'>) =>
      show({ ...options, message, type: 'error' }),
    [show],
  )

  const value = useMemo<ToastContextValue>(
    () => ({ show, info, success, warning, error, dismiss, dismissAll }),
    [show, info, success, warning, error, dismiss, dismissAll],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

// ---------- Internal viewport (not exported) ----------

import { useTranslation } from 'react-i18next'

interface ToastViewportProps {
  toasts: Toast[]
  onDismiss: (id: string) => void
}

function ToastViewport({ toasts, onDismiss }: ToastViewportProps): ReactElement {
  const { t } = useTranslation('toast')
  return (
    <div
      className="eg-toast-viewport"
      role="region"
      aria-label={t('region.label') as string}
      aria-live="polite"
      aria-atomic="false"
      data-testid="eg-toast-viewport"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

import { useEffect } from 'react'

interface ToastItemProps {
  toast: Toast
  onDismiss: (id: string) => void
}

function ToastItem({ toast, onDismiss }: ToastItemProps): ReactElement {
  const { t } = useTranslation('toast')

  useEffect(() => {
    if (toast.duration <= 0) return undefined
    const id = window.setTimeout(() => {
      onDismiss(toast.id)
    }, toast.duration)
    return () => window.clearTimeout(id)
  }, [toast.id, toast.duration, onDismiss])

  const role = toast.type === 'error' || toast.type === 'warning' ? 'alert' : 'status'

  return (
    <div
      className="eg-toast"
      data-tone={toneForType(toast.type)}
      data-type={toast.type}
      role={role}
      data-testid={`eg-toast-${toast.id}`}
    >
      <div className="eg-toast__icon" aria-hidden="true">
        {iconForType(toast.type)}
      </div>
      <div className="eg-toast__body">
        <div className="eg-toast__message">{toast.message}</div>
        {toast.description !== undefined && (
          <div className="eg-toast__description">{toast.description}</div>
        )}
        {toast.action !== undefined && (
          <button
            type="button"
            className="eg-toast__action"
            onClick={() => {
              toast.action?.onClick()
              onDismiss(toast.id)
            }}
          >
            {toast.action.label}
          </button>
        )}
      </div>
      {toast.dismissible && (
        <button
          type="button"
          className="eg-toast__close"
          onClick={() => onDismiss(toast.id)}
          aria-label={t('action.dismiss') as string}
        >
          <span aria-hidden="true">×</span>
        </button>
      )}
    </div>
  )
}

function toneForType(type: ToastType): string {
  switch (type) {
    case 'success':
      return 'trust'
    case 'warning':
      return 'warning'
    case 'error':
      return 'critical'
    default:
      return 'info'
  }
}

function iconForType(type: ToastType): string {
  switch (type) {
    case 'success':
      return '✓'
    case 'warning':
      return '!'
    case 'error':
      return '×'
    default:
      return 'i'
  }
}

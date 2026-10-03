import {
  useCallback,
  useEffect,
  useRef,
  type ReactElement,
  type ReactNode,
} from 'react'
import { useTranslation } from 'react-i18next'

export type DrawerSide = 'start' | 'end'
export type DrawerSize = 'sm' | 'md' | 'lg'

export interface DrawerProps {
  open: boolean
  onClose: () => void
  title: ReactNode
  children: ReactNode
  /** Optional footer (actions). */
  footer?: ReactNode
  /** Side to slide from. Default: 'end' (inline-end in both LTR and RTL). */
  side?: DrawerSide
  /** Width tier. Default: 'md'. */
  size?: DrawerSize
  /** Accessible name override. */
  ariaLabel?: string
}

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function getFocusable(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    (el) => el.offsetParent !== null || el === document.activeElement,
  )
}

/**
 * Drawer — a contextual side panel.
 *
 * Distinct from dialogs and command palettes:
 *   - Slides in from inline-start or inline-end
 *   - Full-height on the side of the viewport
 *   - Focus trap inside the panel
 *   - Closes on Esc, backdrop, or the X button
 *   - RTL-aware (side is inline-based, not left/right)
 *
 * The drawer does NOT decide what to display. It provides structure
 * (header, body, footer) and behavior (focus, trap, escape).
 */
export function Drawer({
  open,
  onClose,
  title,
  children,
  footer,
  side = 'end',
  size = 'md',
  ariaLabel,
}: DrawerProps): ReactElement | null {
  const { t } = useTranslation('drawer')
  const panelRef = useRef<HTMLDivElement | null>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  // Remember and restore focus
  useEffect(() => {
    if (!open) return
    previouslyFocused.current = document.activeElement as HTMLElement | null
    const id = window.requestAnimationFrame(() => {
      const panel = panelRef.current
      if (panel === null) return
      const focusables = getFocusable(panel)
      const first = focusables[0] ?? panel
      first.focus()
    })
    return () => {
      window.cancelAnimationFrame(id)
      const prev = previouslyFocused.current
      if (prev !== null && 'focus' in prev) {
        try {
          prev.focus()
        } catch {
          /* noop */
        }
      }
    }
  }, [open])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }
      if (e.key === 'Tab') {
        const panel = panelRef.current
        if (panel === null) return
        const focusables = getFocusable(panel)
        if (focusables.length === 0) {
          e.preventDefault()
          return
        }
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (first === undefined || last === undefined) return

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    },
    [onClose],
  )

  if (!open) return null

  return (
    <div
      className="eg-drawer-overlay"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      data-testid="eg-drawer-overlay"
    >
      <div
        ref={panelRef}
        className={`eg-drawer eg-drawer--${size} eg-drawer--${side}`}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel ?? (typeof title === 'string' ? title : (t('dialogLabel') as string))}
        data-side={side}
        data-size={size}
        data-testid="eg-drawer"
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        <header className="eg-drawer__header">
          <h2 className="eg-drawer__title">{title}</h2>
          <button
            type="button"
            className="eg-drawer__close"
            onClick={onClose}
            aria-label={t('close') as string}
            title={t('close') as string}
            data-testid="eg-drawer-close"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <div className="eg-drawer__body">{children}</div>

        {footer !== undefined && (
          <footer className="eg-drawer__footer">{footer}</footer>
        )}
      </div>
    </div>
  )
}

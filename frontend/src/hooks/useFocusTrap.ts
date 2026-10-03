/**
 * UI-01.L.2 — Focus trap for modal surfaces.
 *
 * Usage (in a dialog that already handles its own initial focus):
 *
 *   const { handleTabKey } = useFocusTrap({ active: open })
 *   <div role="dialog" onKeyDown={(e) => { handleTabKey(e); ... }}>
 *
 * Behavior:
 *   - `active`: when true, remembers the previously-focused element and
 *     restores focus to it on deactivate / unmount.
 *   - `handleTabKey(e)`: call from the container's onKeyDown. Wraps Tab
 *     and Shift+Tab so focus cannot escape the container.
 *
 * Design notes:
 *   - The container is taken from `e.currentTarget`; no ref needed.
 *   - Initial focus remains the dialog's responsibility (each dialog
 *     already runs its own requestAnimationFrame focus).
 *   - Focusable detection is jsdom-safe: it does NOT rely on offsetParent.
 */

import {
  useEffect,
  useRef,
  type KeyboardEvent as ReactKeyboardEvent,
} from 'react'

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const all = Array.from(
    container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
  )
  return all.filter((el) => {
    if (el === document.activeElement) return true
    if (el.hasAttribute('hidden')) return false
    if (el.getAttribute('aria-hidden') === 'true') return false
    return true
  })
}

export interface UseFocusTrapOptions {
  /** Whether the trap is armed (usually `open`). */
  active: boolean
  /** Whether to restore focus on deactivate. Default: true. */
  restoreFocus?: boolean
}

export interface UseFocusTrapReturn {
  /** Call inside the container's onKeyDown. */
  handleTabKey: (e: ReactKeyboardEvent<HTMLElement>) => void
}

export function useFocusTrap(
  options: UseFocusTrapOptions,
): UseFocusTrapReturn {
  const { active, restoreFocus = true } = options
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!active) return
    previouslyFocused.current = document.activeElement as HTMLElement | null
    return () => {
      if (!restoreFocus) return
      const target = previouslyFocused.current
      if (target && document.contains(target)) {
        target.focus()
      }
    }
  }, [active, restoreFocus])

  function handleTabKey(e: ReactKeyboardEvent<HTMLElement>): void {
    if (e.key !== 'Tab') return
    const container = e.currentTarget
    const focusables = getFocusableElements(container)
    if (focusables.length === 0) {
      e.preventDefault()
      return
    }
    const first = focusables[0]!
    const last = focusables[focusables.length - 1]!
    const current = document.activeElement as HTMLElement | null
    const inside = current !== null && container.contains(current)

    if (e.shiftKey) {
      if (!inside || current === first) {
        e.preventDefault()
        last.focus()
      }
    } else {
      if (!inside || current === last) {
        e.preventDefault()
        first.focus()
      }
    }
  }

  return { handleTabKey }
}

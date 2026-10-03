import { useEffect } from 'react'

export interface ShortcutDef {
  /** Stable id (used for logging / tests). */
  id: string
  /**
   * Human-readable key spec, e.g. "?", "Ctrl+/", "Ctrl+B".
   * Currently used only for the help dialog; the matching is
   * computed from the parsed fields below.
   */
  keys: string
  /** Localized description shown in the shortcuts dialog. */
  description: string
  /** Localized group label. */
  group: string
  /** Match logic — receives the live KeyboardEvent. */
  match: (e: KeyboardEvent) => boolean
  /** Called when the shortcut fires. */
  handler: () => void
}

function isInInput(target: EventTarget | null): boolean {
  if (target === null) return false
  const el = target as HTMLElement
  const tag = el.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (el.isContentEditable === true) return true
  return false
}

/**
 * useKeyboardShortcuts — binds an array of shortcut definitions to
 * window-level keydown events.
 *
 * Behavior:
 *   - Shortcuts with `Ctrl`/`Cmd` modifier fire anywhere, INCLUDING
 *     inside inputs (except when the input is `type="text"` and the
 *     user is typing something that could conflict — Ctrl+B etc. is
 *     safe in text inputs).
 *   - Shortcuts that match a bare printable character (like `?`) are
 *     suppressed when the user is typing in an input, textarea, or
 *     contenteditable element.
 *   - All handlers run in a single keydown listener; no conflicts.
 *
 * The hook is pure: it does not decide what the shortcuts do, only
 * when they fire.
 */
export function useKeyboardShortcuts(shortcuts: ShortcutDef[]): void {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent): void => {
      // Ignore key repeats.
      if (e.repeat) return

      for (const s of shortcuts) {
        // Bare-character shortcuts are suppressed inside inputs.
        const hasModifier = e.ctrlKey || e.metaKey || e.altKey
        if (!hasModifier && isInInput(e.target)) {
          // Only suppress non-modifier shortcuts inside inputs.
          // Modifier shortcuts are always allowed.
          continue
        }
        if (s.match(e)) {
          e.preventDefault()
          s.handler()
          return
        }
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [shortcuts])
}

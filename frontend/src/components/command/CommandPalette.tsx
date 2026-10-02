import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactElement,
  type ReactNode,
} from 'react'
import { useTranslation } from 'react-i18next'

export interface Command {
  /** Stable unique identifier. */
  id: string
  /** Localized label shown in the list. */
  label: string
  /** Group key for visual grouping. Matches command.group.<key> if present. */
  group?: string
  /** Extra search terms (in addition to label). */
  keywords?: string[]
  /** Right-aligned hint, e.g. keyboard shortcut. */
  shortcut?: string
  /** Disable selection. */
  disabled?: boolean
  /** Invoked when the command is chosen. */
  onRun: () => void
}

export interface CommandPaletteProps {
  /** Whether the palette is currently open. */
  open: boolean
  /** Called when the user requests to close (Escape, backdrop, X). */
  onClose: () => void
  /** Commands available to the user. */
  commands: Command[]
  /** Optional title override. */
  title?: ReactNode
  /** Optional placeholder override. */
  placeholder?: string
}

interface IndexedCommand extends Command {
  /** Index in the full commands array for stable ordering. */
  index: number
}

function matches(cmd: IndexedCommand, q: string): boolean {
  if (q === '') return true
  const query = q.toLowerCase()
  if (cmd.label.toLowerCase().includes(query)) return true
  if (cmd.keywords !== undefined) {
    for (const kw of cmd.keywords) {
      if (kw.toLowerCase().includes(query)) return true
    }
  }
  return false
}

/**
 * CommandPalette — Ctrl+K / Cmd+K global command surface.
 *
 * Spec §16. Fully generic: the palette does NOT decide what commands exist.
 * Commands are supplied by the host application; the palette handles:
 *   - Open/close state (controlled)
 *   - Query filtering
 *   - Keyboard navigation (↑/↓/Enter/Escape)
 *   - Accessibility (role=dialog, aria-modal, focus trap on input)
 *   - Group rendering
 *
 * It does NOT fetch data, does NOT know about routing, and does NOT
 * invent commands.
 */
export function CommandPalette({
  open,
  onClose,
  commands,
  title,
  placeholder,
}: CommandPaletteProps): ReactElement | null {
  const { t } = useTranslation('command')
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)

  // Reset query when opening.
  useEffect(() => {
    if (open) {
      setQuery('')
      setActive(0)
    }
  }, [open])

  // Autofocus input when opening.
  useEffect(() => {
    if (!open) return
    const el = inputRef.current
    if (el !== null) {
      // Use requestAnimationFrame to ensure the dialog is mounted.
      const id = window.requestAnimationFrame(() => {
        el.focus()
        el.select()
      })
      return () => window.cancelAnimationFrame(id)
    }
    return undefined
  }, [open])

  // Filtered + indexed commands.
  const indexed: IndexedCommand[] = useMemo(
    () => commands.map((c, i) => ({ ...c, index: i })),
    [commands],
  )
  const filtered = useMemo(
    () => indexed.filter((c) => matches(c, query)),
    [indexed, query],
  )

  // Clamp active index when filtered set changes.
  useEffect(() => {
    if (filtered.length === 0) {
      setActive(0)
      return
    }
    if (active >= filtered.length) {
      setActive(filtered.length - 1)
    }
  }, [filtered.length, active])

  const runCommand = useCallback(
    (cmd: Command | undefined) => {
      if (cmd === undefined || cmd.disabled === true) return
      cmd.onRun()
      onClose()
    },
    [onClose],
  )

  const handleKeyDown = useCallback(
    (e: ReactKeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        if (filtered.length === 0) return
        let next = active
        for (let i = 1; i <= filtered.length; i++) {
          const idx = (active + i) % filtered.length
          if (filtered[idx]?.disabled !== true) {
            next = idx
            break
          }
        }
        setActive(next)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        if (filtered.length === 0) return
        let prev = active
        for (let i = 1; i <= filtered.length; i++) {
          const idx = (active - i + filtered.length) % filtered.length
          if (filtered[idx]?.disabled !== true) {
            prev = idx
            break
          }
        }
        setActive(prev)
        return
      }
      if (e.key === 'Enter') {
        e.preventDefault()
        runCommand(filtered[active])
        return
      }
    },
    [active, filtered, onClose, runCommand],
  )

  // Scroll active item into view.
  useEffect(() => {
    if (!open) return
    const list = listRef.current
    if (list === null) return
    const el = list.querySelector(`[data-cmd-index="${active}"]`)
    if (el !== null && 'scrollIntoView' in el) {
      try {
        ;(el as HTMLElement).scrollIntoView({ block: 'nearest' })
      } catch {
        /* noop */
      }
    }
  }, [active, open])

  if (!open) return null

  const activeId = filtered[active]?.id

  return (
    <div
      className="eg-cmd-overlay"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="eg-cmd"
        role="dialog"
        aria-modal="true"
        aria-label={(typeof title === 'string' ? title : t('title')) as string}
      >
        <div className="eg-cmd__header">
          <span className="eg-cmd__icon" aria-hidden="true">⌘</span>
          <input
            ref={inputRef}
            type="text"
            className="eg-cmd__input"
            placeholder={placeholder ?? (t('placeholder') as string)}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-controls="eg-cmd-listbox"
            aria-activedescendant={activeId !== undefined ? `eg-cmd-opt-${activeId}` : undefined}
            autoComplete="off"
            spellCheck={false}
          />
          <button
            type="button"
            className="eg-cmd__close"
            onClick={onClose}
            aria-label={t('hints.close') as string}
            title={t('hints.close') as string}
          >
            <span aria-hidden="true">×</span>
          </button>
        </div>

        <div ref={listRef} className="eg-cmd__body" id="eg-cmd-listbox" role="listbox">
          {filtered.length === 0 ? (
            <div className="eg-cmd__empty">
              <div className="eg-cmd__empty-title">{t('noResults')}</div>
              <div className="eg-cmd__empty-hint">{t('noResultsHint')}</div>
            </div>
          ) : (
            filtered.map((cmd, i) => {
              const showGroup = i === 0 || filtered[i - 1]?.group !== cmd.group
              const isActive = i === active
              return (
                <div key={cmd.id}>
                  {showGroup && cmd.group !== undefined && (
                    <div className="eg-cmd__group">{t(`group.${cmd.group}`)}</div>
                  )}
                  <div
                    id={`eg-cmd-opt-${cmd.id}`}
                    data-cmd-index={i}
                    role="option"
                    aria-selected={isActive}
                    aria-disabled={cmd.disabled === true ? true : undefined}
                    className={`eg-cmd__item ${isActive ? 'eg-cmd__item--active' : ''} ${cmd.disabled === true ? 'eg-cmd__item--disabled' : ''}`}
                    onClick={() => runCommand(cmd)}
                    onMouseEnter={() => {
                      if (cmd.disabled !== true) setActive(i)
                    }}
                  >
                    <span className="eg-cmd__item-label">{cmd.label}</span>
                    {cmd.shortcut !== undefined && (
                      <span className="eg-cmd__item-shortcut eg-mono">{cmd.shortcut}</span>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>

        <div className="eg-cmd__footer">
          <span className="eg-cmd__hint"><kbd>↑</kbd><kbd>↓</kbd> {t('hints.navigate')}</span>
          <span className="eg-cmd__hint"><kbd>↵</kbd> {t('hints.run')}</span>
          <span className="eg-cmd__hint"><kbd>Esc</kbd> {t('hints.close')}</span>
        </div>
      </div>
    </div>
  )
}

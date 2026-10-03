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
import Fuse from 'fuse.js'

export interface Command {
  id: string
  label: string
  group?: string
  keywords?: string[]
  shortcut?: string
  disabled?: boolean
  onRun: () => void
}

export interface CommandPaletteProps {
  open: boolean
  onClose: () => void
  commands: Command[]
  title?: ReactNode
  placeholder?: string
}

interface IndexedCommand extends Command {
  index: number
}

/**
 * Fuse.js options tuned for the command palette:
 *   - labels weighted higher than keywords
 *   - 0.4 threshold = typo-tolerant but not too loose
 *   - ignoreLocation so the match can be anywhere in the string
 */
const FUSE_OPTIONS = {
  keys: [
    { name: 'label', weight: 0.7 },
    { name: 'keywords', weight: 0.3 },
  ],
  threshold: 0.4,
  ignoreLocation: true,
  minMatchCharLength: 2,
}

/**
 * CommandPalette — Ctrl+K / Cmd+K global command surface.
 *
 * Filtering uses Fuse.js fuzzy matching, so queries tolerate typos
 * ("evidance" matches "Evidence") and partial words. Page descriptions
 * are included as keywords, so content-level queries ("verify evidence")
 * still surface the right navigation command.
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

  useEffect(() => {
    if (open) {
      setQuery('')
      setActive(0)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const el = inputRef.current
    if (el === null) return
    const id = window.requestAnimationFrame(() => {
      el.focus()
      el.select()
    })
    return () => window.cancelAnimationFrame(id)
  }, [open])

  const indexed: IndexedCommand[] = useMemo(
    () => commands.map((c, i) => ({ ...c, index: i })),
    [commands],
  )

  const fuse = useMemo(
    () => new Fuse<IndexedCommand>(indexed, FUSE_OPTIONS),
    [indexed],
  )

  const filtered = useMemo<IndexedCommand[]>(() => {
    if (query === '') return indexed
    return fuse.search(query).map((r) => r.item)
  }, [fuse, query, indexed])

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

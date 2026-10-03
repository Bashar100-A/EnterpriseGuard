import { useCallback, useEffect, useMemo, useRef, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

export interface ShortcutEntry {
  id: string
  /** Localized description. */
  description: string
  /** Localized group label. */
  group: string
  /** Key spec, e.g. "?", "Ctrl+/". */
  keys: string
}

export interface ShortcutsDialogProps {
  open: boolean
  onClose: () => void
  shortcuts: ShortcutEntry[]
}

interface GroupedShortcuts {
  group: string
  items: ShortcutEntry[]
}

function groupByGroup(items: ShortcutEntry[]): GroupedShortcuts[] {
  const map = new Map<string, ShortcutEntry[]>()
  for (const it of items) {
    const arr = map.get(it.group) ?? []
    arr.push(it)
    map.set(it.group, arr)
  }
  return Array.from(map.entries()).map(([group, arr]) => ({ group, items: arr }))
}

/**
 * ShortcutsDialog — spec reference panel for keyboard shortcuts.
 *
 * Opens with `?` or `Ctrl+/`, closes with `Esc`, backdrop click,
 * or the X button. Keyboard-first design; the whole dialog is one
 * `role="dialog"` with a stable accessible name.
 */
export function ShortcutsDialog({
  open,
  onClose,
  shortcuts,
}: ShortcutsDialogProps): ReactElement | null {
  const { t } = useTranslation('shortcuts')
  const dialogRef = useRef<HTMLDivElement | null>(null)

  const groups = useMemo(() => groupByGroup(shortcuts), [shortcuts])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    },
    [onClose],
  )

  useEffect(() => {
    if (!open) return
    const el = dialogRef.current
    if (el === null) return
    const id = window.requestAnimationFrame(() => el.focus())
    return () => window.cancelAnimationFrame(id)
  }, [open])

  if (!open) return null

  return (
    <div
      className="eg-shortcuts-overlay"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={t('title') as string}
        className="eg-shortcuts"
        data-testid="eg-shortcuts-dialog"
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        <header className="eg-shortcuts__header">
          <div className="eg-shortcuts__heading">
            <h2 className="eg-shortcuts__title">{t('title')}</h2>
            <p className="eg-shortcuts__subtitle">{t('subtitle')}</p>
          </div>
          <button
            type="button"
            className="eg-shortcuts__close"
            onClick={onClose}
            aria-label={t('close') as string}
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <div className="eg-shortcuts__body">
          {groups.map((g) => (
            <section key={g.group} className="eg-shortcuts__group">
              <div className="eg-shortcuts__group-title">{g.group}</div>
              <ul className="eg-shortcuts__list" role="list">
                {g.items.map((s) => (
                  <li key={s.id} className="eg-shortcuts__item">
                    <span className="eg-shortcuts__description">{s.description}</span>
                    <span className="eg-shortcuts__keys eg-mono">{s.keys}</span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}

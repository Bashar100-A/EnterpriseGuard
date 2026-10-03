import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useTheme, THEME_MODES } from '../theme'
import { useKeyboardShortcuts, type ShortcutDef } from './useKeyboardShortcuts'

export interface UseGlobalShortcutsOptions {
  onToggleRail?: (() => void) | undefined
  onToggleAssurance?: (() => void) | undefined
  onCloseOverlays?: (() => void) | undefined
}

export interface ShortcutEntryLite {
  id: string
  description: string
  group: string
  keys: string
}

export interface UseGlobalShortcutsReturn {
  /** Whether the shortcuts help dialog is open. */
  helpOpen: boolean
  /** Explicitly close the help dialog. */
  closeHelp: () => void
  /** Entry list for rendering the help dialog. */
  entries: ShortcutEntryLite[]
}

function isPlainKey(e: KeyboardEvent, key: string): boolean {
  return (
    e.key === key &&
    !e.ctrlKey &&
    !e.metaKey &&
    !e.altKey
  )
}

function isCtrlKey(e: KeyboardEvent, key: string): boolean {
  const hasMod = e.ctrlKey || e.metaKey
  return e.key === key && hasMod && !e.altKey
}

function isCtrlShiftKey(e: KeyboardEvent, key: string): boolean {
  const hasMod = e.ctrlKey || e.metaKey
  return e.key.toLowerCase() === key.toLowerCase() && hasMod && e.shiftKey
}

/**
 * useGlobalShortcuts — assembles the app's global shortcut list and
 * manages the shortcuts help dialog state.
 *
 * Shortcuts:
 *   ?          open help
 *   Ctrl+/     open help
 *   Ctrl+B     toggle navigation rail
 *   Ctrl+Shift+A  toggle assurance panel
 *   Ctrl+J     cycle theme
 */
export function useGlobalShortcuts(
  options: UseGlobalShortcutsOptions = {},
): UseGlobalShortcutsReturn {
  const { t } = useTranslation('shortcuts')
  const [helpOpen, setHelpOpen] = useState(false)
  const { mode, setMode } = useTheme()

  const { onToggleRail, onToggleAssurance } = options

  const openHelp = useCallback(() => setHelpOpen(true), [])
  const closeHelp = useCallback(() => setHelpOpen(false), [])

  const cycleTheme = useCallback(() => {
    const idx = THEME_MODES.indexOf(mode)
    const next = THEME_MODES[(idx + 1) % THEME_MODES.length] ?? 'dark'
    setMode(next)
  }, [mode, setMode])

  const shortcuts: ShortcutDef[] = []

  shortcuts.push({
    id: 'help-question',
    keys: '?',
    description: t('shortcuts.openShortcuts') as string,
    group: t('group.help') as string,
    match: (e) => isPlainKey(e, '?'),
    handler: openHelp,
  })

  shortcuts.push({
    id: 'help-slash',
    keys: 'Ctrl + /',
    description: t('shortcuts.openShortcuts') as string,
    group: t('group.help') as string,
    match: (e) => isCtrlKey(e, '/'),
    handler: openHelp,
  })

  if (onToggleRail !== undefined) {
    shortcuts.push({
      id: 'toggle-rail',
      keys: 'Ctrl + B',
      description: t('shortcuts.toggleNavRail') as string,
      group: t('group.interface') as string,
      match: (e) => isCtrlKey(e, 'b') || isCtrlKey(e, 'B'),
      handler: onToggleRail,
    })
  }

  if (onToggleAssurance !== undefined) {
    shortcuts.push({
      id: 'toggle-assurance',
      keys: 'Ctrl + Shift + A',
      description: t('shortcuts.toggleAssurance') as string,
      group: t('group.interface') as string,
      match: (e) => isCtrlShiftKey(e, 'a'),
      handler: onToggleAssurance,
    })
  }

  shortcuts.push({
    id: 'cycle-theme',
    keys: 'Ctrl + J',
    description: t('shortcuts.toggleTheme') as string,
    group: t('group.interface') as string,
    match: (e) => isCtrlKey(e, 'j') || isCtrlKey(e, 'J'),
    handler: cycleTheme,
  })

  useKeyboardShortcuts(shortcuts)

  const entries: ShortcutEntryLite[] = shortcuts.map((s) => ({
    id: s.id,
    description: s.description,
    group: s.group,
    keys: s.keys,
  }))

  return { helpOpen, closeHelp, entries }
}

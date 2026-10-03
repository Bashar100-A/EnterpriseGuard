import { useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { changeLanguage, type SupportedLanguage } from '../i18n'
import { useTheme, type ThemeMode } from '../theme'
import { usePageDescriptions } from './usePageDescriptions'
import type { Command } from '../components/command'

interface RouteEntry {
  path: string
  key: string
}

const ROUTES: RouteEntry[] = [
  { path: '/', key: 'overview' },
  { path: '/operations', key: 'operations' },
  { path: '/intelligence', key: 'intelligence' },
  { path: '/decisions', key: 'decisions' },
  { path: '/evidence', key: 'evidence' },
  { path: '/provenance', key: 'provenance' },
  { path: '/sibb', key: 'sibb' },
  { path: '/policies', key: 'policies' },
  { path: '/governance', key: 'governance' },
  { path: '/approvals', key: 'approvals' },
  { path: '/manifests', key: 'manifests' },
  { path: '/health', key: 'health' },
  { path: '/inspection', key: 'inspection' },
  { path: '/maintenance', key: 'maintenance' },
  { path: '/analytics', key: 'analytics' },
  { path: '/reports', key: 'reports' },
  { path: '/audit', key: 'audit' },
  { path: '/access', key: 'access' },
  { path: '/settings', key: 'settings' },
]

const LANGUAGES: Array<{ code: SupportedLanguage; key: 'languageEnglish' | 'languageArabic' }> = [
  { code: 'en', key: 'languageEnglish' },
  { code: 'ar', key: 'languageArabic' },
]

const THEMES: Array<{ mode: ThemeMode; key: 'themeDark' | 'themeLight' | 'themeSystem' }> = [
  { mode: 'dark', key: 'themeDark' },
  { mode: 'light', key: 'themeLight' },
  { mode: 'system', key: 'themeSystem' },
]

export interface UseCommandsOptions {
  onToggleAssurance?: (() => void) | undefined
  onToggleRail?: (() => void) | undefined
}

/**
 * useCommands — assembles the full list of commands available to the
 * command palette.
 *
 * Each navigation command carries:
 *   - its localized label
 *   - the route path (for direct-path searches)
 *   - the localized page description (for content searches)
 *
 * Fuse.js in the palette can then match queries against labels,
 * keywords, and descriptions, giving fuzzy, typo-tolerant search.
 */
export function useCommands(options: UseCommandsOptions = {}): Command[] {
  const { t } = useTranslation('command')
  const navigate = useNavigate()
  const location = useLocation()
  const { mode, setMode } = useTheme()
  const descriptions = usePageDescriptions()

  const { onToggleAssurance, onToggleRail } = options

  return useMemo<Command[]>(() => {
    const commands: Command[] = []

    for (const route of ROUTES) {
      const isCurrent = route.path === location.pathname
      const description = descriptions[route.path] ?? ''
      const keywords: string[] = [route.path, route.key]
      if (description.length > 0) keywords.push(description)

      commands.push({
        id: `nav-${route.key}`,
        label: t(`commands.${route.key}`) as string,
        group: 'navigate',
        keywords,
        disabled: isCurrent,
        onRun: () => {
          navigate(route.path)
        },
      })
    }

    for (const lang of LANGUAGES) {
      commands.push({
        id: `lang-${lang.code}`,
        label: t(`commands.${lang.key}`) as string,
        group: 'language',
        keywords: [lang.code, 'language', 'locale'],
        onRun: () => {
          void changeLanguage(lang.code)
        },
      })
    }

    for (const theme of THEMES) {
      commands.push({
        id: `theme-${theme.mode}`,
        label: t(`commands.${theme.key}`) as string,
        group: 'theme',
        keywords: [theme.mode, 'theme', 'appearance'],
        disabled: theme.mode === mode,
        onRun: () => {
          setMode(theme.mode)
        },
      })
    }

    if (onToggleAssurance !== undefined) {
      commands.push({
        id: 'ui-toggle-assurance',
        label: t('commands.toggleAssurance') as string,
        group: 'system',
        keywords: ['assurance', 'panel', 'toggle'],
        onRun: onToggleAssurance,
      })
    }

    if (onToggleRail !== undefined) {
      commands.push({
        id: 'ui-toggle-rail',
        label: t('commands.toggleRail') as string,
        group: 'system',
        keywords: ['navigation', 'rail', 'sidebar', 'toggle'],
        onRun: onToggleRail,
      })
    }

    return commands
  }, [t, navigate, location.pathname, mode, setMode, descriptions, onToggleAssurance, onToggleRail])
}

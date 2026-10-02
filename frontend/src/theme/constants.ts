// Pure constants and helpers for the theme module.
// No React, no JSX — safe to import from anywhere.

export const THEME_MODES = ['dark', 'light', 'system'] as const
export type ThemeMode = (typeof THEME_MODES)[number]

export type ResolvedTheme = 'dark' | 'light'

export const DEFAULT_THEME_MODE: ThemeMode = 'dark'
export const THEME_STORAGE_KEY = 'eg.theme'
export const THEME_ATTRIBUTE = 'data-theme'

export function isThemeMode(value: unknown): value is ThemeMode {
  return value === 'dark' || value === 'light' || value === 'system'
}

export function getStoredMode(): ThemeMode {
  if (typeof window === 'undefined') return DEFAULT_THEME_MODE
  const raw = window.localStorage.getItem(THEME_STORAGE_KEY)
  return isThemeMode(raw) ? raw : DEFAULT_THEME_MODE
}

export function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined') return 'dark'
  if (typeof window.matchMedia !== 'function') return 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function resolveTheme(mode: ThemeMode): ResolvedTheme {
  if (mode === 'system') return getSystemTheme()
  return mode
}

export function applyResolvedTheme(resolved: ResolvedTheme): void {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute(THEME_ATTRIBUTE, resolved)
}

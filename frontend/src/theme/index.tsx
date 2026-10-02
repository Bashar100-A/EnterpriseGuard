import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactElement,
  type ReactNode,
} from 'react'

export const THEME_MODES = ['dark', 'light', 'system'] as const
export type ThemeMode = (typeof THEME_MODES)[number]

export type ResolvedTheme = 'dark' | 'light'

export const DEFAULT_THEME_MODE: ThemeMode = 'dark'
export const THEME_STORAGE_KEY = 'eg.theme'
export const THEME_ATTRIBUTE = 'data-theme'

function isThemeMode(value: unknown): value is ThemeMode {
  return value === 'dark' || value === 'light' || value === 'system'
}

function getStoredMode(): ThemeMode {
  if (typeof window === 'undefined') return DEFAULT_THEME_MODE
  const raw = window.localStorage.getItem(THEME_STORAGE_KEY)
  return isThemeMode(raw) ? raw : DEFAULT_THEME_MODE
}

function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined') return 'dark'
  if (typeof window.matchMedia !== 'function') return 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function resolveTheme(mode: ThemeMode): ResolvedTheme {
  if (mode === 'system') return getSystemTheme()
  return mode
}

function applyResolvedTheme(resolved: ResolvedTheme): void {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute(THEME_ATTRIBUTE, resolved)
}

// Apply at module load to avoid flash of wrong theme before React mounts.
if (typeof document !== 'undefined') {
  applyResolvedTheme(resolveTheme(getStoredMode()))
}

interface ThemeContextValue {
  mode: ThemeMode
  resolved: ResolvedTheme
  setMode: (mode: ThemeMode) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

interface ThemeProviderProps {
  children: ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps): ReactElement {
  const [mode, setModeState] = useState<ThemeMode>(() => getStoredMode())
  const [resolved, setResolved] = useState<ResolvedTheme>(() => resolveTheme(getStoredMode()))

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(THEME_STORAGE_KEY, next)
    }
  }, [])

  useEffect(() => {
    const next = resolveTheme(mode)
    setResolved(next)
    applyResolvedTheme(next)
  }, [mode])

  useEffect(() => {
    if (mode !== 'system') return
    if (typeof window === 'undefined') return
    if (typeof window.matchMedia !== 'function') return

    const mql = window.matchMedia('(prefers-color-scheme: dark)')

    const handler = (): void => {
      const next: ResolvedTheme = mql.matches ? 'dark' : 'light'
      setResolved(next)
      applyResolvedTheme(next)
    }

    mql.addEventListener('change', handler)
    return () => {
      mql.removeEventListener('change', handler)
    }
  }, [mode])

  return (
    <ThemeContext.Provider value={{ mode, resolved, setMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme must be used inside <ThemeProvider>')
  }
  return ctx
}

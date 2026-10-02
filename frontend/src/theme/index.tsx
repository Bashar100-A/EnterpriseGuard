import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactElement,
  type ReactNode,
} from 'react'

import {
  applyResolvedTheme,
  getStoredMode,
  resolveTheme,
  type ResolvedTheme,
  type ThemeMode,
} from './constants'

// Apply at module load to avoid a flash of the wrong theme before React
// mounts. Runs once per page load.
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
      window.localStorage.setItem('eg.theme', next)
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

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme must be used inside <ThemeProvider>')
  }
  return ctx
}

// Re-export the constants for ergonomic imports in application code.
export {
  THEME_MODES,
  DEFAULT_THEME_MODE,
  THEME_STORAGE_KEY,
  THEME_ATTRIBUTE,
  isThemeMode,
  getStoredMode,
  getSystemTheme,
  resolveTheme,
  applyResolvedTheme,
  type ThemeMode,
  type ResolvedTheme,
} from './constants'

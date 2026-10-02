import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import type { ReactNode } from 'react'
import {
  ThemeProvider,
  useTheme,
  resolveTheme,
  THEME_MODES,
  THEME_STORAGE_KEY,
  THEME_ATTRIBUTE,
  DEFAULT_THEME_MODE,
} from './index'

function installMatchMedia(matches: boolean): void {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

const wrapper = ({ children }: { children: ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
)

describe('theme infrastructure', () => {
  beforeEach(() => {
    window.localStorage.clear()
    installMatchMedia(false)
    document.documentElement.removeAttribute(THEME_ATTRIBUTE)
  })

  afterEach(() => {
    document.documentElement.removeAttribute(THEME_ATTRIBUTE)
  })

  it('declares dark, light, system as supported modes', () => {
    expect(THEME_MODES).toContain('dark')
    expect(THEME_MODES).toContain('light')
    expect(THEME_MODES).toContain('system')
  })

  it('default mode is dark', () => {
    expect(DEFAULT_THEME_MODE).toBe('dark')
  })

  it('resolveTheme returns literal for dark and light', () => {
    expect(resolveTheme('dark')).toBe('dark')
    expect(resolveTheme('light')).toBe('light')
  })

  it('resolveTheme follows system preference for system mode', () => {
    installMatchMedia(true)
    expect(resolveTheme('system')).toBe('dark')
    installMatchMedia(false)
    expect(resolveTheme('system')).toBe('light')
  })

  it('provider applies data-theme on documentElement at mount', () => {
    renderHook(() => useTheme(), { wrapper })
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('dark')
  })

  it('setMode updates mode, resolved, and documentElement', () => {
    const { result } = renderHook(() => useTheme(), { wrapper })

    act(() => {
      result.current.setMode('light')
    })

    expect(result.current.mode).toBe('light')
    expect(result.current.resolved).toBe('light')
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('light')
  })

  it('setMode persists to localStorage', () => {
    const { result } = renderHook(() => useTheme(), { wrapper })

    act(() => {
      result.current.setMode('light')
    })

    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('system mode resolves to matchMedia result', () => {
    installMatchMedia(false)
    const { result } = renderHook(() => useTheme(), { wrapper })

    act(() => {
      result.current.setMode('system')
    })

    expect(result.current.mode).toBe('system')
    expect(result.current.resolved).toBe('light')
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('light')
  })

  it('ignores invalid persisted values and uses default', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'invalid-value')
    const { result } = renderHook(() => useTheme(), { wrapper })
    expect(result.current.mode).toBe(DEFAULT_THEME_MODE)
  })

  it('useTheme throws when used outside provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => renderHook(() => useTheme())).toThrow(/ThemeProvider/)
    spy.mockRestore()
  })
})

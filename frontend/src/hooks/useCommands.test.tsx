import { describe, it, expect, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { ThemeProvider } from '../theme'
import '../i18n'
import { useCommands } from './useCommands'

function wrapper(initialPath = '/'): ({ children }: { children: ReactNode }) => ReturnType<typeof MemoryRouter> {
  return ({ children }) => (
    <ThemeProvider>
      <MemoryRouter initialEntries={[initialPath]}>{children}</MemoryRouter>
    </ThemeProvider>
  )
}

afterEach(() => {
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('useCommands', () => {
  it('returns commands for all 19 routes', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const navCmds = result.current.filter((c) => c.group === 'navigate')
    expect(navCmds).toHaveLength(19)
  })

  it('returns two language commands', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const langCmds = result.current.filter((c) => c.group === 'language')
    expect(langCmds).toHaveLength(2)
  })

  it('returns three theme commands', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const themeCmds = result.current.filter((c) => c.group === 'theme')
    expect(themeCmds).toHaveLength(3)
  })

  it('does NOT include UI toggle commands when callbacks are absent', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const systemCmds = result.current.filter((c) => c.group === 'system')
    expect(systemCmds).toHaveLength(0)
  })

  it('includes assurance toggle when callback is provided', () => {
    const cb = vi.fn()
    const { result } = renderHook(
      () => useCommands({ onToggleAssurance: cb }),
      { wrapper: wrapper() },
    )
    const systemCmds = result.current.filter((c) => c.group === 'system')
    expect(systemCmds.length).toBeGreaterThanOrEqual(1)
    const assurance = systemCmds.find((c) => c.id === 'ui-toggle-assurance')
    expect(assurance).toBeDefined()
  })

  it('includes rail toggle when callback is provided', () => {
    const cb = vi.fn()
    const { result } = renderHook(
      () => useCommands({ onToggleRail: cb }),
      { wrapper: wrapper() },
    )
    const rail = result.current.find((c) => c.id === 'ui-toggle-rail')
    expect(rail).toBeDefined()
  })

  it('marks the current route command as disabled', () => {
    const { result } = renderHook(() => useCommands(), {
      wrapper: wrapper('/evidence'),
    })
    const evidenceCmd = result.current.find((c) => c.id === 'nav-evidence')
    expect(evidenceCmd?.disabled).toBe(true)
  })

  it('does NOT mark other route commands as disabled', () => {
    const { result } = renderHook(() => useCommands(), {
      wrapper: wrapper('/evidence'),
    })
    const overviewCmd = result.current.find((c) => c.id === 'nav-overview')
    expect(overviewCmd?.disabled).toBeFalsy()
  })

  it('marks the current theme as disabled', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const darkCmd = result.current.find((c) => c.id === 'theme-dark')
    expect(darkCmd?.disabled).toBe(true)
  })

  it('calls the toggle callback when the command is run', () => {
    const cb = vi.fn()
    const { result } = renderHook(
      () => useCommands({ onToggleAssurance: cb }),
      { wrapper: wrapper() },
    )
    const assurance = result.current.find((c) => c.id === 'ui-toggle-assurance')
    act(() => {
      assurance?.onRun()
    })
    expect(cb).toHaveBeenCalledTimes(1)
  })

  it('every command has a non-empty label', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    for (const cmd of result.current) {
      expect(cmd.label).toBeTruthy()
      expect(typeof cmd.label).toBe('string')
    }
  })

  it('every command has a unique id', () => {
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const ids = result.current.map((c) => c.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('renders in Arabic (labels are translated)', async () => {
    const { changeLanguage } = await import('../i18n')
    await changeLanguage('ar')
    const { result } = renderHook(() => useCommands(), { wrapper: wrapper() })
    const overviewCmd = result.current.find((c) => c.id === 'nav-overview')
    expect(overviewCmd?.label).toContain('نظرة عامة')
    await changeLanguage('en')
  })
})

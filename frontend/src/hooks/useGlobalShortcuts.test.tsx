import { describe, it, expect, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { ThemeProvider } from '../theme'
import '../i18n'
import { useGlobalShortcuts } from './useGlobalShortcuts'

function wrapper({ children }: { children: ReactNode }): ReturnType<typeof MemoryRouter> {
  return (
    <ThemeProvider>
      <MemoryRouter>{children}</MemoryRouter>
    </ThemeProvider>
  )
}

function pressKey(init: KeyboardEventInit): void {
  const e = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init })
  window.dispatchEvent(e)
}

afterEach(() => {
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('useGlobalShortcuts', () => {
  it('starts with help closed', () => {
    const { result } = renderHook(() => useGlobalShortcuts(), { wrapper })
    expect(result.current.helpOpen).toBe(false)
  })

  it('? opens help', () => {
    const { result } = renderHook(() => useGlobalShortcuts(), { wrapper })
    act(() => pressKey({ key: '?' }))
    expect(result.current.helpOpen).toBe(true)
  })

  it('Ctrl+/ opens help', () => {
    const { result } = renderHook(() => useGlobalShortcuts(), { wrapper })
    act(() => pressKey({ key: '/', ctrlKey: true }))
    expect(result.current.helpOpen).toBe(true)
  })

  it('closeHelp closes the dialog', () => {
    const { result } = renderHook(() => useGlobalShortcuts(), { wrapper })
    act(() => pressKey({ key: '?' }))
    expect(result.current.helpOpen).toBe(true)
    act(() => result.current.closeHelp())
    expect(result.current.helpOpen).toBe(false)
  })

  it('Ctrl+B fires the rail toggle', () => {
    const toggle = vi.fn()
    renderHook(
      () => useGlobalShortcuts({ onToggleRail: toggle }),
      { wrapper },
    )
    act(() => pressKey({ key: 'b', ctrlKey: true }))
    expect(toggle).toHaveBeenCalledTimes(1)
  })

  it('Ctrl+Shift+A fires the assurance toggle', () => {
    const toggle = vi.fn()
    renderHook(
      () => useGlobalShortcuts({ onToggleAssurance: toggle }),
      { wrapper },
    )
    act(() => pressKey({ key: 'A', ctrlKey: true, shiftKey: true }))
    expect(toggle).toHaveBeenCalledTimes(1)
  })

  it('entries always include the help shortcuts', () => {
    const { result } = renderHook(() => useGlobalShortcuts(), { wrapper })
    const ids = result.current.entries.map((e) => e.id)
    expect(ids).toContain('help-question')
    expect(ids).toContain('help-slash')
  })

  it('entries include rail toggle only when callback is provided', () => {
    const a = renderHook(() => useGlobalShortcuts(), { wrapper })
    expect(a.result.current.entries.find((e) => e.id === 'toggle-rail')).toBeUndefined()
  })

  it('entries include rail toggle when callback is provided', () => {
    const { result } = renderHook(
      () => useGlobalShortcuts({ onToggleRail: () => {} }),
      { wrapper },
    )
    expect(result.current.entries.find((e) => e.id === 'toggle-rail')).toBeDefined()
  })

  it('all entries have non-empty description, group, keys', () => {
    const { result } = renderHook(() => useGlobalShortcuts(), { wrapper })
    for (const e of result.current.entries) {
      expect(e.description).toBeTruthy()
      expect(e.group).toBeTruthy()
      expect(e.keys).toBeTruthy()
    }
  })
})

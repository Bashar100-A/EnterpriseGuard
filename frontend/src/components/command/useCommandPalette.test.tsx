import { describe, it, expect, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCommandPalette } from './useCommandPalette'

afterEach(() => {
  window.localStorage.clear()
})

function pressCtrlK(): void {
  const e = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true })
  window.dispatchEvent(e)
}

function pressCmdK(): void {
  const e = new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true })
  window.dispatchEvent(e)
}

function pressK(): void {
  const e = new KeyboardEvent('keydown', { key: 'k', bubbles: true })
  window.dispatchEvent(e)
}

describe('useCommandPalette', () => {
  it('starts closed', () => {
    const { result } = renderHook(() => useCommandPalette())
    expect(result.current.open).toBe(false)
  })

  it('setOpen(true) opens the palette', () => {
    const { result } = renderHook(() => useCommandPalette())
    act(() => result.current.setOpen(true))
    expect(result.current.open).toBe(true)
  })

  it('toggle flips the state', () => {
    const { result } = renderHook(() => useCommandPalette())
    act(() => result.current.toggle())
    expect(result.current.open).toBe(true)
    act(() => result.current.toggle())
    expect(result.current.open).toBe(false)
  })

  it('Ctrl+K toggles the state', () => {
    const { result } = renderHook(() => useCommandPalette())
    act(() => pressCtrlK())
    expect(result.current.open).toBe(true)
    act(() => pressCtrlK())
    expect(result.current.open).toBe(false)
  })

  it('Cmd+K toggles the state', () => {
    const { result } = renderHook(() => useCommandPalette())
    act(() => pressCmdK())
    expect(result.current.open).toBe(true)
  })

  it('plain K does NOT toggle', () => {
    const { result } = renderHook(() => useCommandPalette())
    act(() => pressK())
    expect(result.current.open).toBe(false)
  })

  it('uppercase K works too', () => {
    const { result } = renderHook(() => useCommandPalette())
    act(() => {
      const e = new KeyboardEvent('keydown', { key: 'K', ctrlKey: true, bubbles: true })
      window.dispatchEvent(e)
    })
    expect(result.current.open).toBe(true)
  })

  it('cleans up the listener on unmount', () => {
    const { result, unmount } = renderHook(() => useCommandPalette())
    act(() => pressCtrlK())
    expect(result.current.open).toBe(true)
    unmount()
    // After unmount, a new Ctrl+K should NOT crash and should not affect
    // anything (we can't check the old hook's state, but we ensure no throw).
    expect(() => pressCtrlK()).not.toThrow()
  })
})

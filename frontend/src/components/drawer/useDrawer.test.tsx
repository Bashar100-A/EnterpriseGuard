import { describe, it, expect, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDrawer } from './useDrawer'

afterEach(() => {
  window.localStorage.clear()
})

describe('useDrawer', () => {
  it('starts closed with no payload', () => {
    const { result } = renderHook(() => useDrawer())
    expect(result.current.open).toBe(false)
    expect(result.current.payload).toBeUndefined()
  })

  it('openDrawer opens without a payload', () => {
    const { result } = renderHook(() => useDrawer())
    act(() => result.current.openDrawer())
    expect(result.current.open).toBe(true)
    expect(result.current.payload).toBeUndefined()
  })

  it('openDrawer stores a payload', () => {
    const { result } = renderHook(() => useDrawer<{ id: string }>())
    act(() => result.current.openDrawer({ id: 'ev-42' }))
    expect(result.current.open).toBe(true)
    expect(result.current.payload).toEqual({ id: 'ev-42' })
  })

  it('closeDrawer closes but keeps the payload', () => {
    const { result } = renderHook(() => useDrawer<{ id: string }>())
    act(() => result.current.openDrawer({ id: 'ev-42' }))
    act(() => result.current.closeDrawer())
    expect(result.current.open).toBe(false)
    // Payload persists until next open
    expect(result.current.payload).toEqual({ id: 'ev-42' })
  })

  it('toggleDrawer opens when closed', () => {
    const { result } = renderHook(() => useDrawer())
    act(() => result.current.toggleDrawer())
    expect(result.current.open).toBe(true)
  })

  it('toggleDrawer closes when open', () => {
    const { result } = renderHook(() => useDrawer())
    act(() => result.current.openDrawer())
    expect(result.current.open).toBe(true)
    act(() => result.current.toggleDrawer())
    expect(result.current.open).toBe(false)
  })

  it('toggleDrawer sets the payload when opening', () => {
    const { result } = renderHook(() => useDrawer<{ id: string }>())
    act(() => result.current.toggleDrawer({ id: 'a' }))
    expect(result.current.payload).toEqual({ id: 'a' })
  })

  it('reopening replaces the payload', () => {
    const { result } = renderHook(() => useDrawer<{ id: string }>())
    act(() => result.current.openDrawer({ id: 'a' }))
    act(() => result.current.openDrawer({ id: 'b' }))
    expect(result.current.payload).toEqual({ id: 'b' })
  })
})

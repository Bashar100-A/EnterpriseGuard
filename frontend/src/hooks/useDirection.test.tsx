import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useDirection, getDocumentDirection } from './useDirection'

describe('useDirection hook', () => {
  beforeEach(() => {
    document.documentElement.dir = 'ltr'
    document.documentElement.lang = 'en'
  })

  afterEach(() => {
    document.documentElement.dir = 'ltr'
    document.documentElement.lang = 'en'
  })

  it('getDocumentDirection returns ltr when html[dir] is ltr', () => {
    document.documentElement.dir = 'ltr'
    expect(getDocumentDirection()).toBe('ltr')
  })

  it('getDocumentDirection returns rtl when html[dir] is rtl', () => {
    document.documentElement.dir = 'rtl'
    expect(getDocumentDirection()).toBe('rtl')
  })

  it('defaults to ltr when dir attribute is empty or invalid', () => {
    document.documentElement.removeAttribute('dir')
    expect(getDocumentDirection()).toBe('ltr')
    document.documentElement.dir = 'invalid'
    expect(getDocumentDirection()).toBe('ltr')
  })

  it('hook reflects initial direction', () => {
    document.documentElement.dir = 'ltr'
    const { result } = renderHook(() => useDirection())
    expect(result.current).toBe('ltr')
  })

  it('hook updates when html[dir] changes to rtl', async () => {
    document.documentElement.dir = 'ltr'
    const { result } = renderHook(() => useDirection())

    act(() => {
      document.documentElement.dir = 'rtl'
    })

    await waitFor(() => {
      expect(result.current).toBe('rtl')
    })
  })

  it('hook updates when html[dir] changes back to ltr', async () => {
    document.documentElement.dir = 'rtl'
    const { result } = renderHook(() => useDirection())
    expect(result.current).toBe('rtl')

    act(() => {
      document.documentElement.dir = 'ltr'
    })

    await waitFor(() => {
      expect(result.current).toBe('ltr')
    })
  })

  it('hook does not respond to unrelated attribute changes', async () => {
    document.documentElement.dir = 'ltr'
    const { result } = renderHook(() => useDirection())

    act(() => {
      document.documentElement.setAttribute('data-theme', 'light')
      document.documentElement.setAttribute('lang', 'ar')
    })

    // Give MutationObserver a microtask to fire
    await new Promise((r) => setTimeout(r, 10))
    expect(result.current).toBe('ltr')
  })
})

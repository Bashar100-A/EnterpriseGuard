import { describe, it, expect, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import '../i18n'
import { usePageDescriptions } from './usePageDescriptions'
import { PAGES } from '../search/pageIndex'

afterEach(() => {
  window.localStorage.clear()
})

describe('usePageDescriptions', () => {
  it('returns a description for every page path', () => {
    const { result } = renderHook(() => usePageDescriptions())
    for (const p of PAGES) {
      expect(result.current[p.path]).toBeDefined()
      expect(typeof result.current[p.path]).toBe('string')
    }
  })

  it('returns the English description for /evidence', () => {
    const { result } = renderHook(() => usePageDescriptions())
    expect(result.current['/evidence']).toMatch(/Verified and unverified/i)
  })

  it('returns the English description for /sibb', () => {
    const { result } = renderHook(() => usePageDescriptions())
    expect(result.current['/sibb']).toMatch(/integrity foundation/i)
  })

  it('returns the Arabic description after language change', async () => {
    const { changeLanguage } = await import('../i18n')
    await changeLanguage('ar')
    const { result } = renderHook(() => usePageDescriptions())
    // Evidence description in Arabic — contains "موثّقة"
    expect(result.current['/evidence']).toMatch(/موثّقة|الأدلة/)
    await changeLanguage('en')
  })

  it('covers exactly the number of pages listed in PAGES', () => {
    const { result } = renderHook(() => usePageDescriptions())
    const keys = Object.keys(result.current)
    expect(keys.length).toBe(PAGES.length)
  })
})

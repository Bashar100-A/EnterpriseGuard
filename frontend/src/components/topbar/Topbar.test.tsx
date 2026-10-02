import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { Topbar } from './Topbar'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  document.documentElement.removeAttribute('data-theme')
  window.localStorage.clear()
})

describe('Topbar', () => {
  beforeEach(async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('en')
    window.localStorage.clear()
  })

  it('renders the vendor name', () => {
    renderWithProviders(<Topbar />)
    expect(screen.getByText('EnterpriseGuard')).toBeTruthy()
  })

  it('renders a breadcrumb home label', () => {
    renderWithProviders(<Topbar />)
    expect(screen.getByText('Home')).toBeTruthy()
  })

  it('renders the search trigger (disabled)', () => {
    renderWithProviders(<Topbar />)
    const search = screen.getByRole('button', { name: /Search/i })
    expect(search.hasAttribute('disabled')).toBe(true)
  })

  it('shows environment from Vite MODE', () => {
    renderWithProviders(<Topbar />)
    expect(screen.getByText(/Test/i)).toBeTruthy()
  })

  it('shows system state as Unknown', () => {
    renderWithProviders(<Topbar />)
    const badge = document.querySelector('[data-state="unknown"]')
    expect(badge?.textContent).toContain('Unknown')
  })

  it('renders EN and AR language buttons', () => {
    renderWithProviders(<Topbar />)
    expect(screen.getByRole('button', { name: 'EN' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'AR' })).toBeTruthy()
  })

  it('clicking AR switches language and updates document direction', async () => {
    renderWithProviders(<Topbar />)
    fireEvent.click(screen.getByRole('button', { name: 'AR' }))
    await new Promise((r) => setTimeout(r, 20))
    expect(document.documentElement.dir).toBe('rtl')
    expect(document.documentElement.lang).toBe('ar')
  })

  it('renders a theme cycle button', () => {
    renderWithProviders(<Topbar />)
    expect(screen.getByRole('button', { name: /Cycle theme/i })).toBeTruthy()
  })

  it('clicking theme button changes data-theme-mode', () => {
    renderWithProviders(<Topbar />)
    const themeBtn = screen.getByRole('button', { name: /Cycle theme/i })
    expect(themeBtn.getAttribute('data-theme-mode')).toBe('dark')
    fireEvent.click(themeBtn)
    const updated = screen.getByRole('button', { name: /Cycle theme/i })
    expect(updated.getAttribute('data-theme-mode')).toBe('light')
  })

  it('renders a disabled user slot', () => {
    renderWithProviders(<Topbar />)
    const userBtn = screen.getByRole('button', { name: /User/i })
    expect(userBtn.hasAttribute('disabled')).toBe(true)
  })

  it('does NOT render assurance toggle when handler is absent', () => {
    renderWithProviders(<Topbar />)
    expect(screen.queryByRole('button', { name: /Open assurance panel/i })).toBeNull()
  })

  it('renders assurance toggle and calls handler when clicked', () => {
    const handler = vi.fn()
    renderWithProviders(<Topbar onToggleAssurance={handler} />)
    const btn = screen.getByRole('button', { name: /Open assurance panel/i })
    fireEvent.click(btn)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('assurance toggle has aria-pressed=false when closed', () => {
    renderWithProviders(
      <Topbar onToggleAssurance={() => {}} assuranceOpen={false} />,
    )
    const btn = screen.getByRole('button', { name: /Open assurance panel/i })
    expect(btn.getAttribute('aria-pressed')).toBe('false')
  })

  it('assurance toggle has aria-pressed=true when open', () => {
    renderWithProviders(
      <Topbar onToggleAssurance={() => {}} assuranceOpen={true} />,
    )
    const btn = screen.getByRole('button', { name: /Close assurance panel/i })
    expect(btn.getAttribute('aria-pressed')).toBe('true')
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithProviders(<Topbar />)
    expect(screen.getByText('EnterpriseGuard')).toBeTruthy()
  })
})

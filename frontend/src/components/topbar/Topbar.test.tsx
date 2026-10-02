import { describe, it, expect, afterEach, beforeEach } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import '../../i18n'
import { ThemeProvider } from '../../theme'
import { Topbar } from './Topbar'

function renderTopbar(props: { currentPath?: string } = {}): ReturnType<typeof render> {
  return render(
    <ThemeProvider>
      <Topbar {...props} />
    </ThemeProvider>,
  )
}

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
    renderTopbar()
    expect(screen.getByText('EnterpriseGuard')).toBeTruthy()
  })

  it('renders a breadcrumb home label', () => {
    renderTopbar()
    expect(screen.getByText('Home')).toBeTruthy()
  })

  it('renders the search trigger (disabled)', () => {
    renderTopbar()
    const search = screen.getByRole('button', { name: /Search/i })
    expect(search).toBeTruthy()
    expect(search.hasAttribute('disabled')).toBe(true)
  })

  it('shows environment from Vite MODE (test → Test)', () => {
    renderTopbar()
    // Vitest sets MODE='test'
    expect(screen.getByText(/Test/i)).toBeTruthy()
  })

  it('shows system state as Unknown (no fake healthy)', () => {
    renderTopbar()
    const badge = document.querySelector('[data-state="unknown"]')
    expect(badge).not.toBeNull()
    expect(badge?.textContent).toContain('Unknown')
  })

  it('renders EN and AR language buttons', () => {
    renderTopbar()
    expect(screen.getByRole('button', { name: 'EN' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'AR' })).toBeTruthy()
  })

  it('EN is marked active by default', () => {
    renderTopbar()
    const en = screen.getByRole('button', { name: 'EN' })
    expect(en.getAttribute('aria-pressed')).toBe('true')
  })

  it('clicking AR switches language and updates document direction', async () => {
    renderTopbar()
    fireEvent.click(screen.getByRole('button', { name: 'AR' }))
    // Language change is async; give the event loop a tick
    await new Promise((r) => setTimeout(r, 20))
    expect(document.documentElement.dir).toBe('rtl')
    expect(document.documentElement.lang).toBe('ar')
  })

  it('renders a theme cycle button', () => {
    renderTopbar()
    const themeBtn = screen.getByRole('button', { name: /Cycle theme/i })
    expect(themeBtn).toBeTruthy()
  })

  it('clicking theme button changes data-theme-mode', () => {
    renderTopbar()
    const themeBtn = screen.getByRole('button', { name: /Cycle theme/i })
    const initialMode = themeBtn.getAttribute('data-theme-mode')
    expect(initialMode).toBe('dark')
    fireEvent.click(themeBtn)
    const updatedBtn = screen.getByRole('button', { name: /Cycle theme/i })
    expect(updatedBtn.getAttribute('data-theme-mode')).toBe('light')
  })

  it('renders a disabled user slot', () => {
    renderTopbar()
    const userBtn = screen.getByRole('button', { name: /User/i })
    expect(userBtn).toBeTruthy()
    expect(userBtn.hasAttribute('disabled')).toBe(true)
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderTopbar()
    expect(screen.getByText('EnterpriseGuard')).toBeTruthy()
  })

  it('renders with custom currentPath', () => {
    renderTopbar({ currentPath: '/evidence' })
    expect(screen.getByText(/evidence/i)).toBeTruthy()
  })
})

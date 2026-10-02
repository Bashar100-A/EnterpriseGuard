import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import type { ReactElement } from 'react'
import App from '../app/App'
import { ThemeProvider } from '../theme'

/**
 * The production entry point (main.tsx) wraps App in ThemeProvider.
 * Tests must do the same, because Topbar (rendered by App) uses useTheme().
 */
function renderApp(): ReturnType<typeof render> {
  return render(<ThemeProvider><App /></ThemeProvider> as ReactElement)
}

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  document.documentElement.removeAttribute('data-theme')
  window.localStorage.clear()
})

describe('App (UI-01 foundation)', () => {
  it('renders the foundation title', () => {
    renderApp()
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })

  it('renders foundation status', () => {
    renderApp()
    expect(screen.getByText(/Foundation Ready/i)).toBeTruthy()
  })

  it('declares no operational data is connected', () => {
    renderApp()
    expect(screen.getByText(/no operational data connected/i)).toBeTruthy()
  })

  it('wraps content in AppShell', () => {
    const { container } = renderApp()
    expect(container.querySelector('.eg-shell')).not.toBeNull()
  })

  it('has a semantic main landmark', () => {
    const { container } = renderApp()
    expect(container.querySelector('main#eg-main')).not.toBeNull()
  })

  it('includes the NavigationRail', () => {
    const { container } = renderApp()
    expect(container.querySelector('nav.eg-nav')).not.toBeNull()
  })

  it('includes the Topbar', () => {
    const { container } = renderApp()
    expect(container.querySelector('.eg-topbar')).not.toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderApp()
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })
})

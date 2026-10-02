import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderApp } from './renderWithProviders'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  document.documentElement.removeAttribute('data-theme')
  window.localStorage.clear()
})

describe('App (UI-01 foundation, routed)', () => {
  it('renders the shell at root', () => {
    const { container } = renderApp(['/'])
    expect(container.querySelector('.eg-shell')).not.toBeNull()
  })

  it('renders a semantic main landmark', () => {
    const { container } = renderApp(['/'])
    expect(container.querySelector('main#eg-main')).not.toBeNull()
  })

  it('includes the NavigationRail', () => {
    const { container } = renderApp(['/'])
    expect(container.querySelector('nav.eg-nav')).not.toBeNull()
  })

  it('includes the Topbar', () => {
    const { container } = renderApp(['/'])
    expect(container.querySelector('.eg-topbar')).not.toBeNull()
  })

  it('renders the Overview page title at /', () => {
    renderApp(['/'])
    expect(screen.getAllByText('Overview').length).toBeGreaterThan(0)
  })

  it('renders the Evidence page title at /evidence', () => {
    renderApp(['/evidence'])
    expect(screen.getAllByText('Evidence').length).toBeGreaterThan(0)
  })

  it('renders NotFound at unknown path', () => {
    renderApp(['/does-not-exist'])
    expect(screen.getByText(/Not Found/i)).toBeTruthy()
  })

  it('navigates to another route when clicking a nav item', async () => {
    const { container } = renderApp(['/'])
    const evidenceBtn = Array.from(container.querySelectorAll('button.eg-nav__item'))
      .find((b) => b.textContent?.includes('Evidence'))
    expect(evidenceBtn).toBeDefined()
    ;(evidenceBtn as HTMLButtonElement).click()
    await new Promise((r) => setTimeout(r, 30))
    const h1 = document.querySelector('.eg-workspace__title')
    expect(h1?.textContent).toBe('Evidence')
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    const { container } = renderApp(['/'])
    expect(container.querySelector('.eg-shell')).not.toBeNull()
  })
})

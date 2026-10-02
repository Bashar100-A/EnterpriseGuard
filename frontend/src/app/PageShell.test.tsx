import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../test/renderWithProviders'
import { PageShell } from './PageShell'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  window.localStorage.clear()
})

describe('PageShell', () => {
  it('renders the title from navigation.items key', () => {
    renderWithThemeOnly(<PageShell titleKey="overview" groupKey="command" />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Overview')
  })

  it('renders breadcrumb with group and page', () => {
    renderWithThemeOnly(<PageShell titleKey="evidence" groupKey="trust" />)
    expect(screen.getByText('Trust')).toBeTruthy()
    // Title appears in both breadcrumb and h1
    expect(screen.getAllByText('Evidence').length).toBeGreaterThan(0)
  })

  it('renders assurance badge as Unknown', () => {
    const { container } = renderWithThemeOnly(<PageShell titleKey="audit" groupKey="assurance" />)
    const badge = container.querySelector('.eg-workspace__assurance')
    expect(badge?.getAttribute('data-state')).toBe('unknown')
  })

  it('renders ContextStrip', () => {
    const { container } = renderWithThemeOnly(<PageShell titleKey="overview" groupKey="command" />)
    expect(container.querySelector('.eg-context')).not.toBeNull()
  })

  it('renders foundation placeholder note', () => {
    renderWithThemeOnly(<PageShell titleKey="overview" groupKey="command" />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<PageShell titleKey="overview" groupKey="command" />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })
})

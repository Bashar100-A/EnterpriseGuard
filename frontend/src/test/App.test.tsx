import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import App from '../app/App'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  window.localStorage.clear()
})

describe('App (UI-01 foundation)', () => {
  it('renders the foundation title', () => {
    render(<App />)
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })

  it('renders foundation status (UI-01 Foundation)', () => {
    render(<App />)
    expect(screen.getByText(/Foundation Ready/i)).toBeTruthy()
  })

  it('declares no operational data is connected', () => {
    render(<App />)
    expect(screen.getByText(/no operational data connected/i)).toBeTruthy()
  })

  it('wraps content in AppShell (eg-shell class present)', () => {
    const { container } = render(<App />)
    expect(container.querySelector('.eg-shell')).not.toBeNull()
  })

  it('provides a semantic main landmark with id eg-main', () => {
    const { container } = render(<App />)
    expect(container.querySelector('main#eg-main')).not.toBeNull()
  })

  it('includes the NavigationRail', () => {
    const { container } = render(<App />)
    expect(container.querySelector('nav.eg-nav')).not.toBeNull()
  })

  it('renders without error when document is set to RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    render(<App />)
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })
})

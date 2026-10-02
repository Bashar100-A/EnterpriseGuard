import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import App from '../app/App'

// Explicit cleanup between tests. Vitest is configured without
// `globals: true`, so RTL cannot auto-register its cleanup hook.
afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
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

  it('renders without error when document is set to RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    render(<App />)
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })

  it('root element is a <main> landmark in both directions', () => {
    document.documentElement.dir = 'ltr'
    const { container: ltrContainer } = render(<App />)
    expect(ltrContainer.querySelector('main')).not.toBeNull()
    cleanup()

    document.documentElement.dir = 'rtl'
    const { container: rtlContainer } = render(<App />)
    expect(rtlContainer.querySelector('main')).not.toBeNull()
  })
})

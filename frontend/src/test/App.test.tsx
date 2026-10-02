import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import App from '../app/App'

// UI-01.B.1 — explicit cleanup between tests.
// Vitest is configured without `globals: true`, so RTL cannot auto-register
// its cleanup hook. This afterEach guarantees each test unmounts its tree
// and no duplicate containers remain in document.body.
afterEach(() => {
  cleanup()
})

describe('App (UI-01.B.1 foundation)', () => {
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
})

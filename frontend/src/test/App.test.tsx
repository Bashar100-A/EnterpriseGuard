import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import App from '../app/App'
import { renderWithProviders } from './renderWithProviders'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  document.documentElement.removeAttribute('data-theme')
  window.localStorage.clear()
})

describe('App (UI-01 foundation)', () => {
  it('renders the foundation title', () => {
    renderWithProviders(<App />)
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })

  it('renders foundation status', () => {
    renderWithProviders(<App />)
    expect(screen.getByText(/Foundation Ready/i)).toBeTruthy()
  })

  it('declares no operational data is connected', () => {
    renderWithProviders(<App />)
    expect(screen.getByText(/no operational data connected/i)).toBeTruthy()
  })

  it('wraps content in AppShell', () => {
    const { container } = renderWithProviders(<App />)
    expect(container.querySelector('.eg-shell')).not.toBeNull()
  })

  it('has a semantic main landmark', () => {
    const { container } = renderWithProviders(<App />)
    expect(container.querySelector('main#eg-main')).not.toBeNull()
  })

  it('includes the NavigationRail', () => {
    const { container } = renderWithProviders(<App />)
    expect(container.querySelector('nav.eg-nav')).not.toBeNull()
  })

  it('includes the Topbar', () => {
    const { container } = renderWithProviders(<App />)
    expect(container.querySelector('.eg-topbar')).not.toBeNull()
  })

  it('includes the WorkspaceHeader', () => {
    const { container } = renderWithProviders(<App />)
    expect(container.querySelector('.eg-workspace')).not.toBeNull()
  })

  it('includes the ContextStrip', () => {
    const { container } = renderWithProviders(<App />)
    expect(container.querySelector('.eg-context')).not.toBeNull()
  })

  it('renders the assurance badge as Unknown by default', () => {
    const { container } = renderWithProviders(<App />)
    const badge = container.querySelector('.eg-workspace__assurance')
    expect(badge).not.toBeNull()
    expect(badge?.getAttribute('data-state')).toBe('unknown')
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithProviders(<App />)
    expect(screen.getByText(/Sovereign Control Surface/i)).toBeTruthy()
  })
})

import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderApp } from '../test/renderWithProviders'
import { ROUTE_SPECS } from './router'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  window.localStorage.clear()
})

describe('router', () => {
  it('declares 20 routes', () => {
    expect(ROUTE_SPECS).toHaveLength(20)
  })

  it('every route has a unique path', () => {
    const paths = ROUTE_SPECS.map((r) => r.path)
    expect(new Set(paths).size).toBe(paths.length)
  })

  it('root path is /', () => {
    expect(ROUTE_SPECS[0]?.path).toBe('/')
  })

  it('renders Overview at /', () => {
    renderApp(['/'])
    expect(screen.getAllByText('Overview').length).toBeGreaterThan(0)
  })

  it('renders Evidence at /evidence', () => {
    renderApp(['/evidence'])
    expect(screen.getAllByText('Evidence').length).toBeGreaterThan(0)
  })

  it('renders Audit at /audit', () => {
    renderApp(['/audit'])
    expect(screen.getAllByText('Audit').length).toBeGreaterThan(0)
  })

  it('renders NotFound at an unknown path', () => {
    renderApp(['/no-such-page-xyz'])
    expect(screen.getByText(/Not Found/i)).toBeTruthy()
  })

  it('topbar shows the current path breadcrumb tail', () => {
    const { container } = renderApp(['/evidence'])
    const tail = container.querySelector('.eg-topbar__crumb-tail')
    expect(tail?.textContent).toBe('evidence')
  })
})

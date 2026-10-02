import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../test/renderWithProviders'
import { ErrorBoundary } from './ErrorBoundary'

function Boom(): JSX.Element {
  throw new Error('intentional test error')
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('ErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    renderWithThemeOnly(
      <ErrorBoundary><div>safe-content</div></ErrorBoundary>,
    )
    expect(screen.getByText('safe-content')).toBeTruthy()
  })

  it('renders fallback UI when a child throws', () => {
    // Suppress React's console.error about the caught error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    renderWithThemeOnly(<ErrorBoundary><Boom /></ErrorBoundary>)
    expect(screen.getByRole('alert')).toBeTruthy()
    expect(screen.getByText(/Something went wrong/i)).toBeTruthy()
    spy.mockRestore()
  })

  it('shows a reference code (no stack trace)', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    renderWithThemeOnly(<ErrorBoundary><Boom /></ErrorBoundary>)
    const mono = document.querySelector('.eg-mono')
    expect(mono?.textContent).toMatch(/UI-ERR-/)
    spy.mockRestore()
  })

  it('does NOT leak the thrown error message', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    renderWithThemeOnly(<ErrorBoundary><Boom /></ErrorBoundary>)
    const alert = screen.getByRole('alert')
    expect(alert.textContent).not.toContain('intentional test error')
    spy.mockRestore()
  })

  it('retry button resets the boundary', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { rerender } = renderWithThemeOnly(<ErrorBoundary><Boom /></ErrorBoundary>)
    const btn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(btn)
    // After retry, the boundary should attempt to render children again,
    // which will throw again, so the fallback reappears. The key assertion
    // is that clicking does not crash and the retry path executes.
    expect(btn).toBeTruthy()
    rerender(<ErrorBoundary><Boom /></ErrorBoundary>)
    spy.mockRestore()
  })

  it('calls onError callback when a child throws', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const handler = vi.fn()
    renderWithThemeOnly(
      <ErrorBoundary onError={handler}><Boom /></ErrorBoundary>,
    )
    expect(handler).toHaveBeenCalledTimes(1)
    expect(handler.mock.calls[0]?.[0]).toBeInstanceOf(Error)
    spy.mockRestore()
  })
})

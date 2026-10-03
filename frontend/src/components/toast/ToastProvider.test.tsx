import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent, act } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { useToast } from './useToast'
import type { ToastContextValue } from './types'

function Probe({ onReady }: { onReady: (api: ToastContextValue) => void }): null {
  const api = useToast()
  onReady(api)
  return null
}

function renderProbe(): { current: ToastContextValue | null } {
  const ref: { current: ToastContextValue | null } = { current: null }
  renderWithThemeOnly(
    <Probe
      onReady={(api) => {
        ref.current = api
      }}
    />,
  )
  return ref
}

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('ToastProvider', () => {
  it('renders a viewport with role=region and aria-live=polite', () => {
    renderProbe()
    const viewport = screen.getByTestId('eg-toast-viewport')
    expect(viewport.getAttribute('role')).toBe('region')
    expect(viewport.getAttribute('aria-live')).toBe('polite')
  })

  it('starts with no toasts', () => {
    renderProbe()
    const viewport = screen.getByTestId('eg-toast-viewport')
    expect(viewport.children.length).toBe(0)
  })

  it('show() creates a toast', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Hello')
    })
    expect(screen.getByText('Hello')).toBeTruthy()
  })

  it('info/success/warning/error each render their message', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Info-msg')
      ref.current?.success('Success-msg')
      ref.current?.warning('Warning-msg')
      ref.current?.error('Error-msg')
    })
    expect(screen.getByText('Info-msg')).toBeTruthy()
    expect(screen.getByText('Success-msg')).toBeTruthy()
    expect(screen.getByText('Warning-msg')).toBeTruthy()
    expect(screen.getByText('Error-msg')).toBeTruthy()
  })

  it('success type gets tone=trust', () => {
    const ref = renderProbe()
    let id = ''
    act(() => {
      id = ref.current?.success('Success') ?? ''
    })
    const toast = screen.getByTestId(`eg-toast-${id}`)
    expect(toast.getAttribute('data-tone')).toBe('trust')
  })

  it('error type gets tone=critical and role=alert', () => {
    const ref = renderProbe()
    let id = ''
    act(() => {
      id = ref.current?.error('Error') ?? ''
    })
    const toast = screen.getByTestId(`eg-toast-${id}`)
    expect(toast.getAttribute('data-tone')).toBe('critical')
    expect(toast.getAttribute('role')).toBe('alert')
  })

  it('warning type gets tone=warning and role=alert', () => {
    const ref = renderProbe()
    let id = ''
    act(() => {
      id = ref.current?.warning('Warn') ?? ''
    })
    const toast = screen.getByTestId(`eg-toast-${id}`)
    expect(toast.getAttribute('data-tone')).toBe('warning')
    expect(toast.getAttribute('role')).toBe('alert')
  })

  it('info type gets tone=info and role=status', () => {
    const ref = renderProbe()
    let id = ''
    act(() => {
      id = ref.current?.info('Info') ?? ''
    })
    const toast = screen.getByTestId(`eg-toast-${id}`)
    expect(toast.getAttribute('data-tone')).toBe('info')
    expect(toast.getAttribute('role')).toBe('status')
  })

  it('dismiss(id) removes the toast', () => {
    const ref = renderProbe()
    let id = ''
    act(() => {
      id = ref.current?.info('Bye') ?? ''
    })
    expect(screen.getByText('Bye')).toBeTruthy()
    act(() => {
      ref.current?.dismiss(id)
    })
    expect(screen.queryByText('Bye')).toBeNull()
  })

  it('dismissAll removes all toasts', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('A')
      ref.current?.info('B')
    })
    expect(screen.getByText('A')).toBeTruthy()
    expect(screen.getByText('B')).toBeTruthy()
    act(() => {
      ref.current?.dismissAll()
    })
    expect(screen.queryByText('A')).toBeNull()
    expect(screen.queryByText('B')).toBeNull()
  })

  it('close button dismisses the toast', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Close me')
    })
    const closeBtn = screen.getByRole('button', { name: /Dismiss notification/i })
    fireEvent.click(closeBtn)
    expect(screen.queryByText('Close me')).toBeNull()
  })

  it('dismissible=false hides the close button', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Sticky', { dismissible: false })
    })
    expect(screen.queryByRole('button', { name: /Dismiss notification/i })).toBeNull()
  })

  it('renders description when provided', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Title', { description: 'Detailed message' })
    })
    expect(screen.getByText('Detailed message')).toBeTruthy()
  })

  it('action button fires onClick and dismisses', () => {
    const ref = renderProbe()
    const onClick = vi.fn()
    act(() => {
      ref.current?.info('With action', {
        action: { label: 'Undo', onClick },
      })
    })
    const btn = screen.getByRole('button', { name: 'Undo' })
    fireEvent.click(btn)
    expect(onClick).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('With action')).toBeNull()
  })

  it('auto-dismisses after the specified duration', () => {
    vi.useFakeTimers()
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Auto', { duration: 1000 })
    })
    expect(screen.getByText('Auto')).toBeTruthy()

    // Advance fake timers inside act() so React processes the state update.
    act(() => {
      vi.advanceTimersByTime(1100)
    })

    // No waitFor() — fake timers and waitFor don't mix.
    expect(screen.queryByText('Auto')).toBeNull()
  })

  it('duration=0 disables auto-dismiss', () => {
    vi.useFakeTimers()
    const ref = renderProbe()
    act(() => {
      ref.current?.info('Persistent', { duration: 0 })
    })
    act(() => {
      vi.advanceTimersByTime(60000)
    })
    expect(screen.getByText('Persistent')).toBeTruthy()
  })

  it('uses default duration per type (error=8000ms)', () => {
    vi.useFakeTimers()
    const ref = renderProbe()
    act(() => {
      ref.current?.error('Err')
    })
    // At 7000ms the error should still be visible
    act(() => {
      vi.advanceTimersByTime(7000)
    })
    expect(screen.getByText('Err')).toBeTruthy()
    // At 8500ms it should be gone
    act(() => {
      vi.advanceTimersByTime(1500)
    })
    expect(screen.queryByText('Err')).toBeNull()
  })

  it('multiple toasts render in order', () => {
    const ref = renderProbe()
    act(() => {
      ref.current?.info('First')
      ref.current?.info('Second')
      ref.current?.info('Third')
    })
    const viewport = screen.getByTestId('eg-toast-viewport')
    const messages = Array.from(viewport.querySelectorAll('.eg-toast__message'))
    expect(messages.map((m) => m.textContent)).toEqual(['First', 'Second', 'Third'])
  })

  it('useToast throws outside a provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {
      // silence the React error boundary log
    })

    function Bare(): null {
      useToast()
      return null
    }

    expect(() => render(<Bare />)).toThrow(/ToastProvider/)
    spy.mockRestore()
  })
})

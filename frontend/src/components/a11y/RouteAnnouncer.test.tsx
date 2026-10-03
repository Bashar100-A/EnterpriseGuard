import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import type { ReactElement } from 'react'

import '../../i18n'
import { RouteAnnouncer } from './RouteAnnouncer'

afterEach(() => {
  cleanup()
  document.title = ''
})

function Harness(): ReactElement {
  const navigate = useNavigate()
  return (
    <>
      <RouteAnnouncer />
      <button data-testid="go-evidence" onClick={() => navigate('/evidence')}>
        E
      </button>
      <button data-testid="go-health" onClick={() => navigate('/health')}>
        H
      </button>
      <button data-testid="go-root" onClick={() => navigate('/')}>
        R
      </button>
      <button data-testid="go-unknown" onClick={() => navigate('/does-not-exist')}>
        U
      </button>
    </>
  )
}

function renderHarness(initial: string[] = ['/']) {
  return render(
    <MemoryRouter initialEntries={initial}>
      <Harness />
    </MemoryRouter>,
  )
}

describe('RouteAnnouncer — live region', () => {
  it('renders a status region', () => {
    renderHarness()
    expect(screen.getByTestId('route-announcer')).toBeTruthy()
    expect(screen.getByTestId('route-announcer').getAttribute('role')).toBe('status')
  })

  it('uses aria-live="polite"', () => {
    renderHarness()
    expect(
      screen.getByTestId('route-announcer').getAttribute('aria-live'),
    ).toBe('polite')
  })

  it('uses aria-atomic="true"', () => {
    renderHarness()
    expect(
      screen.getByTestId('route-announcer').getAttribute('aria-atomic'),
    ).toBe('true')
  })

  it('is visually hidden', () => {
    renderHarness()
    expect(
      screen.getByTestId('route-announcer').className,
    ).toContain('eg-visually-hidden')
  })
})

describe('RouteAnnouncer — initial mount', () => {
  it('announces the root page title on mount', async () => {
    renderHarness(['/'])
    await waitFor(() => {
      expect(screen.getByTestId('route-announcer').textContent).toMatch(/Overview/)
    })
  })

  it('sets document.title on mount', async () => {
    renderHarness(['/'])
    await waitFor(() => {
      expect(document.title).toContain('Overview')
    })
  })

  it('announces the deep-linked page title on mount', async () => {
    renderHarness(['/evidence'])
    await waitFor(() => {
      expect(screen.getByTestId('route-announcer').textContent).toMatch(/Evidence/)
    })
  })
})

describe('RouteAnnouncer — route change', () => {
  it('announces when navigating to /evidence', async () => {
    renderHarness(['/'])
    fireEvent.click(screen.getByTestId('go-evidence'))
    await waitFor(() => {
      expect(screen.getByTestId('route-announcer').textContent).toMatch(/Evidence/)
    })
  })

  it('updates document.title after navigation', async () => {
    renderHarness(['/'])
    fireEvent.click(screen.getByTestId('go-health'))
    await waitFor(() => {
      expect(document.title).toContain('System Health')
    })
  })

  it('announces when navigating back to root', async () => {
    renderHarness(['/evidence'])
    await waitFor(() => {
      expect(screen.getByTestId('route-announcer').textContent).toMatch(/Evidence/)
    })
    fireEvent.click(screen.getByTestId('go-root'))
    await waitFor(() => {
      expect(screen.getByTestId('route-announcer').textContent).toMatch(/Overview/)
    })
  })

  it('includes the "Navigated to" prefix from i18n', async () => {
    renderHarness(['/'])
    fireEvent.click(screen.getByTestId('go-evidence'))
    await waitFor(() => {
      const text = screen.getByTestId('route-announcer').textContent ?? ''
      expect(text.toLowerCase()).toMatch(/navigated to/)
    })
  })
})

describe('RouteAnnouncer — unknown routes', () => {
  it('announces the fallback message for an unknown path', async () => {
    renderHarness(['/'])
    fireEvent.click(screen.getByTestId('go-unknown'))
    await waitFor(() => {
      const text = screen.getByTestId('route-announcer').textContent ?? ''
      expect(text.toLowerCase()).toMatch(/page changed/)
    })
  })

  it('sets document.title to app title for unknown path', async () => {
    renderHarness(['/'])
    fireEvent.click(screen.getByTestId('go-unknown'))
    await waitFor(() => {
      expect(document.title).toContain('EnterpriseGuard')
    })
  })
})

describe('RouteAnnouncer — invariants', () => {
  it('renders exactly one announcer element', () => {
    renderHarness()
    expect(screen.getAllByTestId('route-announcer').length).toBe(1)
  })

  it('does not fetch or use fixtures', () => {
    const { container } = renderHarness()
    expect(container.querySelector('table')).toBeNull()
    expect(container.querySelector('.eg-metric')).toBeNull()
  })
})

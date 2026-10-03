import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { TokenViewerPage } from './TokenViewerPage'
import { renderWithProviders } from '../../test/renderWithProviders'
import {
  TOKEN_GROUPS,
  TOTAL_TOKENS,
  THEME_DEPENDENT,
} from './tokens'

afterEach(() => {
  cleanup()
})

describe('TokenViewerPage — structure', () => {
  it('renders the tokens region', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getByTestId('tokens-region')).toBeTruthy()
  })

  it('region has the Design Tokens aria-label', () => {
    renderWithProviders(<TokenViewerPage />)
    const r = screen.getByTestId('tokens-region')
    expect(r.getAttribute('aria-label')).toBe('Design Tokens')
    expect(r.getAttribute('role')).toBe('region')
  })

  it('renders an h2 heading', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getByRole('heading', { level: 2 })).toBeTruthy()
  })

  it('renders one group per TOKEN_GROUPS entry', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    const groups = container.querySelectorAll('.eg-tokens__group')
    expect(groups.length).toBe(TOKEN_GROUPS.length)
  })

  it('renders exactly TOTAL_TOKENS chips', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    expect(container.querySelectorAll('.eg-tokens__chip').length).toBe(
      TOTAL_TOKENS,
    )
  })
})

describe('TokenViewerPage — groups present', () => {
  for (const group of TOKEN_GROUPS) {
    it(`renders ${group.key} group`, () => {
      renderWithProviders(<TokenViewerPage />)
      expect(screen.getByTestId(`tokens-group-${group.key}`)).toBeTruthy()
    })
  }
})

describe('TokenViewerPage — token values', () => {
  it('shows the semantic color value #10b981', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText('#10b981').length).toBeGreaterThan(0)
  })

  it('shows the spacing value 4px', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText('4px').length).toBeGreaterThan(0)
  })

  it('shows the typography value 14px', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText('14px').length).toBeGreaterThan(0)
  })

  it('labels theme-dependent tokens honestly', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText(THEME_DEPENDENT).length).toBeGreaterThan(0)
  })

  it('shows the semantic color token name', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText('--eg-trust-emerald').length).toBeGreaterThan(0)
  })

  it('shows the radius token name', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText('--eg-radius-md').length).toBeGreaterThan(0)
  })

  it('shows the font-family token name', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(screen.getAllByText('--eg-font-mono').length).toBeGreaterThan(0)
  })
})

describe('TokenViewerPage — preview kinds', () => {
  it('renders 5 color swatches for semantic colors', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    const semanticGroup = container.querySelector(
      '[data-testid="tokens-group-semanticColors"]',
    )
    expect(semanticGroup?.querySelectorAll('.eg-tokens__swatch').length).toBe(5)
  })

  it('renders spacing bars in the spacing group', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    const group = container.querySelector('[data-testid="tokens-group-spacing"]')
    expect(group?.querySelectorAll('.eg-tokens__bar').length).toBe(4)
  })

  it('renders radius boxes in the radius group', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    const group = container.querySelector('[data-testid="tokens-group-radius"]')
    expect(group?.querySelectorAll('.eg-tokens__box').length).toBe(4)
  })

  it('renders type samples in the typography group', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    const group = container.querySelector(
      '[data-testid="tokens-group-typography"]',
    )
    expect(group?.querySelectorAll('.eg-tokens__sample').length).toBe(6)
  })
})

describe('TokenViewerPage — no leakage', () => {
  it('does not fetch or use fixtures', () => {
    const { container } = renderWithProviders(<TokenViewerPage />)
    expect(container.querySelector('table')).toBeNull()
    expect(container.querySelector('.eg-metric')).toBeNull()
    expect(container.querySelector('.eg-chartframe')).toBeNull()
  })

  it('renders without AdapterProvider', () => {
    render(<TokenViewerPage />)
    expect(screen.getByTestId('tokens-region')).toBeTruthy()
  })

  it('renders the backend note', () => {
    renderWithProviders(<TokenViewerPage />)
    expect(
      screen.getAllByText(/Backend integration comes in a later phase/).length,
    ).toBeGreaterThan(0)
  })
})

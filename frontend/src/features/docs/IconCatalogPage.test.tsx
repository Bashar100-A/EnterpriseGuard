import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { IconCatalogPage } from './IconCatalogPage'
import { renderWithProviders } from '../../test/renderWithProviders'
import {
  ADOPTED_ICONS,
  CANDIDATE_ICONS,
  TOTAL_ADOPTED,
  TOTAL_CANDIDATES,
} from './icons'

afterEach(() => {
  cleanup()
})

describe('IconCatalogPage — structure', () => {
  it('renders the icons region', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.getByTestId('icons-region')).toBeTruthy()
  })

  it('region has the Icon Catalog aria-label', () => {
    renderWithProviders(<IconCatalogPage />)
    const r = screen.getByTestId('icons-region')
    expect(r.getAttribute('aria-label')).toBe('Icon Catalog')
    expect(r.getAttribute('role')).toBe('region')
  })

  it('renders an h2 heading', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.getByRole('heading', { level: 2 })).toBeTruthy()
  })

  it('renders 2 h3 section headings', () => {
    const { container } = renderWithProviders(<IconCatalogPage />)
    expect(container.querySelectorAll('.eg-icons__section-title').length).toBe(2)
  })

  it('renders without AdapterProvider', () => {
    render(<IconCatalogPage />)
    expect(screen.getByTestId('icons-region')).toBeTruthy()
  })
})

describe('IconCatalogPage — honest empty state (current reality)', () => {
  it('registry is currently empty (invariant check)', () => {
    expect(TOTAL_ADOPTED).toBe(0)
    expect(TOTAL_CANDIDATES).toBe(0)
    expect(ADOPTED_ICONS.length).toBe(0)
    expect(CANDIDATE_ICONS.length).toBe(0)
  })

  it('shows the adopted empty note', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.getByTestId('icons-empty-adopted')).toBeTruthy()
  })

  it('shows the candidates empty note', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.getByTestId('icons-empty-candidates')).toBeTruthy()
  })

  it('does NOT render the adopted grid when empty', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.queryByTestId('icons-adopted-grid')).toBeNull()
  })

  it('does NOT render the candidates grid when empty', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.queryByTestId('icons-candidates-grid')).toBeNull()
  })

  it('shows the honest adopted empty title', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(
      screen.getAllByText(/No icons have been adopted/i).length,
    ).toBeGreaterThan(0)
  })

  it('shows the honest candidates empty title', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(
      screen.getAllByText(/No icons are currently under consideration/i).length,
    ).toBeGreaterThan(0)
  })
})

describe('IconCatalogPage — counts', () => {
  it('shows (0) next to adopted', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(screen.getAllByText('(0)').length).toBeGreaterThanOrEqual(2)
  })

  it('does not render any icon card (no fabricated entries)', () => {
    const { container } = renderWithProviders(<IconCatalogPage />)
    expect(container.querySelectorAll('.eg-icons__card').length).toBe(0)
  })
})

describe('IconCatalogPage — content', () => {
  it('renders the philosophy paragraph', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(
      screen.getAllByText(/icon-light/i).length,
    ).toBeGreaterThan(0)
  })

  it('renders the backend note', () => {
    renderWithProviders(<IconCatalogPage />)
    expect(
      screen.getAllByText(/Backend integration comes in a later phase/).length,
    ).toBeGreaterThan(0)
  })

  it('does not fetch or use fixtures', () => {
    const { container } = renderWithProviders(<IconCatalogPage />)
    expect(container.querySelector('table')).toBeNull()
    expect(container.querySelector('.eg-metric')).toBeNull()
    expect(container.querySelector('.eg-chartframe')).toBeNull()
  })
})

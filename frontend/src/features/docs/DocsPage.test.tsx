import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { DocsPage } from './DocsPage'
import { renderWithProviders } from '../../test/renderWithProviders'

afterEach(() => {
  cleanup()
})

describe('DocsPage — structure', () => {
  it('renders the docs region', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByTestId('docs-region')).toBeTruthy()
  })

  it('region has the Documentation aria-label', () => {
    renderWithProviders(<DocsPage />)
    const region = screen.getByTestId('docs-region')
    expect(region.getAttribute('aria-label')).toBe('Documentation')
    expect(region.getAttribute('role')).toBe('region')
  })

  it('renders an h2 heading', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByRole('heading', { level: 2 })).toBeTruthy()
  })

  it('renders the description paragraph', () => {
    renderWithProviders(<DocsPage />)
    expect(
      screen.getAllByText(/Living design system reference/).length,
    ).toBeGreaterThan(0)
  })

  it('renders exactly 4 section cards', () => {
    const { container } = renderWithProviders(<DocsPage />)
    expect(container.querySelectorAll('.eg-docs__card').length).toBe(4)
  })

  it('renders playground card', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByTestId('docs-card-playground')).toBeTruthy()
  })

  it('renders tokens card', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByTestId('docs-card-tokens')).toBeTruthy()
  })

  it('renders icons card', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByTestId('docs-card-icons')).toBeTruthy()
  })

  it('renders semantics card', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByTestId('docs-card-semantics')).toBeTruthy()
  })
})

describe('DocsPage — content', () => {
  it('renders all four section titles', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getByText('Component Playground')).toBeTruthy()
    expect(screen.getByText('Design Tokens')).toBeTruthy()
    expect(screen.getByText('Icon Catalog')).toBeTruthy()
    expect(screen.getByText('Semantic Guide')).toBeTruthy()
  })

  it('renders comingSoon footnote on every card', () => {
    renderWithProviders(<DocsPage />)
    expect(screen.getAllByText('Details coming in a later step.').length).toBe(4)
  })

  it('renders the backend note', () => {
    renderWithProviders(<DocsPage />)
    expect(
      screen.getAllByText(/Backend integration comes in a later phase/).length,
    ).toBeGreaterThan(0)
  })

  it('does not fetch or display any fixture data', () => {
    const { container } = renderWithProviders(<DocsPage />)
    expect(container.querySelector('table')).toBeNull()
    expect(container.querySelector('.eg-metric')).toBeNull()
    expect(container.querySelector('.eg-chart-frame')).toBeNull()
  })
})

describe('DocsPage — accessibility', () => {
  it('every card is an article with an h3 heading', () => {
    const { container } = renderWithProviders(<DocsPage />)
    const cards = container.querySelectorAll('article.eg-docs__card')
    expect(cards.length).toBe(4)
    for (const c of Array.from(cards)) {
      expect(c.querySelector('h3')).not.toBeNull()
    }
  })

  it('renders without AdapterProvider (bare render)', () => {
    render(<DocsPage />)
    expect(screen.getByTestId('docs-region')).toBeTruthy()
  })
})

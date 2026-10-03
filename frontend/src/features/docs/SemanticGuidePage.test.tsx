import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { SemanticGuidePage } from './SemanticGuidePage'
import { renderWithProviders } from '../../test/renderWithProviders'
import { SEMANTIC_TONES } from '../../components/security'

afterEach(() => {
  cleanup()
})

describe('SemanticGuidePage — structure', () => {
  it('renders the semantics region', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByTestId('semantics-region')).toBeTruthy()
  })

  it('region has the Semantic Guide aria-label', () => {
    renderWithProviders(<SemanticGuidePage />)
    const r = screen.getByTestId('semantics-region')
    expect(r.getAttribute('aria-label')).toBe('Semantic Guide')
    expect(r.getAttribute('role')).toBe('region')
  })

  it('renders an h2 heading', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByRole('heading', { level: 2 })).toBeTruthy()
  })

  it('renders 4 h3 section headings', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-semantics__section-title').length).toBe(4)
  })

  it('renders without AdapterProvider', () => {
    render(<SemanticGuidePage />)
    expect(screen.getByTestId('semantics-region')).toBeTruthy()
  })
})

describe('SemanticGuidePage — five tones', () => {
  it('renders exactly 5 tone chips', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-semantics__tone').length).toBe(5)
  })

  it('renders exactly SEMANTIC_TONES.length chips (invariant)', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-semantics__tone').length).toBe(
      SEMANTIC_TONES.length,
    )
  })

  for (const tone of SEMANTIC_TONES) {
    it(`renders the ${tone} tone`, () => {
      renderWithProviders(<SemanticGuidePage />)
      expect(screen.getByTestId(`semantic-tone-${tone}`)).toBeTruthy()
    })
  }

  it('shows the trust token name', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getAllByText('--eg-trust-emerald').length).toBeGreaterThan(0)
  })

  it('shows the unknown token name', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getAllByText('--eg-unknown-gray').length).toBeGreaterThan(0)
  })

  it('renders 5 swatches', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-semantics__swatch').length).toBe(5)
  })
})

describe('SemanticGuidePage — golden rule', () => {
  it('renders the golden rule blockquote', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByTestId('semantics-golden-rule')).toBeTruthy()
  })

  it('states that unknown never becomes trust', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(
      screen.getAllByText(/Unknown never silently becomes Trust/i).length,
    ).toBeGreaterThan(0)
  })

  it('shows both correct and incorrect examples', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByText('Correct')).toBeTruthy()
    expect(screen.getByText('Incorrect')).toBeTruthy()
  })
})

describe('SemanticGuidePage — ADIE separation', () => {
  it('renders 4 separation pairs', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-semantics__pair').length).toBe(4)
  })

  it('renders observed / decided pair', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByTestId('semantic-pair-observed-decided')).toBeTruthy()
  })

  it('renders decided / executed pair', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByTestId('semantic-pair-decided-executed')).toBeTruthy()
  })

  it('renders evidence / authority pair', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByTestId('semantic-pair-evidence-authority')).toBeTruthy()
  })

  it('renders prediction / decision pair', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(screen.getByTestId('semantic-pair-prediction-decision')).toBeTruthy()
  })
})

describe('SemanticGuidePage — examples section', () => {
  it('renders status example rows', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-semantics__example-row').length).toBe(3)
  })

  it('uses StatusBadge for examples', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelectorAll('.eg-badge').length).toBeGreaterThan(0)
  })
})

describe('SemanticGuidePage — no leakage', () => {
  it('does not fetch or use fixtures', () => {
    const { container } = renderWithProviders(<SemanticGuidePage />)
    expect(container.querySelector('table')).toBeNull()
    expect(container.querySelector('.eg-metric')).toBeNull()
    expect(container.querySelector('.eg-chartframe')).toBeNull()
  })

  it('renders the backend note', () => {
    renderWithProviders(<SemanticGuidePage />)
    expect(
      screen.getAllByText(/Backend integration comes in a later phase/).length,
    ).toBeGreaterThan(0)
  })
})

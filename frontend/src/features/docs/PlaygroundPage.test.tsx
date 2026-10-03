import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { PlaygroundPage } from './PlaygroundPage'
import { renderWithProviders } from '../../test/renderWithProviders'
import { evidenceListFixture, isFixture } from '../../services/designFixtures'

afterEach(() => {
  cleanup()
})

describe('PlaygroundPage — structure', () => {
  it('renders the playground region', () => {
    renderWithProviders(<PlaygroundPage />)
    expect(screen.getByTestId('playground-region')).toBeTruthy()
  })

  it('region has an aria-label', () => {
    renderWithProviders(<PlaygroundPage />)
    const r = screen.getByTestId('playground-region')
    expect(r.getAttribute('aria-label')).toBe('Component Playground')
    expect(r.getAttribute('role')).toBe('region')
  })

  it('renders an h2 heading', () => {
    renderWithProviders(<PlaygroundPage />)
    expect(screen.getByRole('heading', { level: 2 })).toBeTruthy()
  })

  it('renders 6 section h3 headings', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    expect(container.querySelectorAll('.eg-playground__section-title').length).toBe(6)
  })
})

describe('PlaygroundPage — badge coverage', () => {
  it('renders 4 status badges', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    const badges = container.querySelectorAll('.eg-badge')
    expect(badges.length).toBeGreaterThanOrEqual(4)
  })

  it('shows all 5 severity levels via labels', () => {
    renderWithProviders(<PlaygroundPage />)
    // at least one of each severity should be visible (labels via i18n)
    for (const level of ['info', 'low', 'medium', 'high', 'critical']) {
      const matches = screen.queryAllByText(new RegExp(level, 'i'))
      expect(matches.length).toBeGreaterThan(0)
    }
  })

  it('shows all 5 environments', () => {
    renderWithProviders(<PlaygroundPage />)
    for (const env of ['Production', 'Staging', 'Development', 'Test', 'Unknown']) {
      expect(screen.getAllByText(env).length).toBeGreaterThan(0)
    }
  })
})

describe('PlaygroundPage — data display', () => {
  it('renders 4 metric cards', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('all metric cards are not-connected (show —)', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders a fixture-backed table', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    expect(container.querySelector('.eg-table')).toBeTruthy()
  })

  it('table has one row per fixture item', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    const rows = container.querySelectorAll('.eg-table tbody tr')
    expect(rows.length).toBe(evidenceListFixture.page.items.length)
  })

  it('fixture is marked (safety check)', () => {
    expect(isFixture(evidenceListFixture)).toBe(true)
  })
})

describe('PlaygroundPage — states', () => {
  it('renders 4 DataState placeholders', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    const states = container.querySelectorAll('.eg-datastate')
    expect(states.length).toBeGreaterThanOrEqual(4)
  })

  it('renders a ChartFrame', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    expect(container.querySelector('.eg-chartframe')).toBeTruthy()
  })
})

describe('PlaygroundPage — no leakage', () => {
  it('no fetch adapters used (renders bare)', () => {
    expect(() => render(<PlaygroundPage />)).not.toThrow()
  })

  it('does not render a full app shell (self-contained region)', () => {
    const { container } = renderWithProviders(<PlaygroundPage />)
    expect(container.querySelector('.eg-shell')).toBeNull()
  })

  it('renders the backend note', () => {
    renderWithProviders(<PlaygroundPage />)
    expect(
      screen.getAllByText(/design reference/i).length,
    ).toBeGreaterThan(0)
  })
})

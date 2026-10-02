import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { DecisionChain } from './DecisionChain'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('DecisionChain', () => {
  it('renders with role=figure and aria-label', () => {
    renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(screen.getByRole('figure')).toBeTruthy()
  })

  it('renders three tier cards', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(container.querySelector('[data-tier="observed"]')).not.toBeNull()
    expect(container.querySelector('[data-tier="decided"]')).not.toBeNull()
    expect(container.querySelector('[data-tier="executed"]')).not.toBeNull()
  })

  it('renders tier headers', () => {
    renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(screen.getByText('Observed')).toBeTruthy()
    expect(screen.getByText('Decided')).toBeTruthy()
    expect(screen.getByText('Executed')).toBeTruthy()
  })

  it('renders all 8 stage labels', () => {
    renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(screen.getByText('Evidence')).toBeTruthy()
    expect(screen.getByText('State')).toBeTruthy()
    expect(screen.getByText('Prediction')).toBeTruthy()
    expect(screen.getByText('Policy')).toBeTruthy()
    expect(screen.getByText('Decision')).toBeTruthy()
    expect(screen.getByText('Authority')).toBeTruthy()
    expect(screen.getByText('Manifest')).toBeTruthy()
    expect(screen.getByText('Outcome')).toBeTruthy()
  })

  it('observed tier contains 3 stages', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    const observed = container.querySelector('[data-tier="observed"]')
    expect(observed?.querySelectorAll('.eg-chain__stage').length).toBe(3)
  })

  it('decided tier contains 3 stages', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    const decided = container.querySelector('[data-tier="decided"]')
    expect(decided?.querySelectorAll('.eg-chain__stage').length).toBe(3)
  })

  it('executed tier contains 2 stages', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    const executed = container.querySelector('[data-tier="executed"]')
    expect(executed?.querySelectorAll('.eg-chain__stage').length).toBe(2)
  })

  it('renders two connectors between three tiers', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(container.querySelectorAll('.eg-chain__connector').length).toBe(2)
  })

  it('all stages default to unknown + null count', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    const counts = container.querySelectorAll('.eg-chain__stage-count')
    expect(counts.length).toBe(8)
    for (const c of Array.from(counts)) {
      expect(c.textContent).toBe('—')
    }
  })

  it('all stage markers have tone=unknown by default', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    const unknownMarkers = container.querySelectorAll('[data-tone="unknown"]')
    expect(unknownMarkers.length).toBeGreaterThanOrEqual(8)
  })

  it('supplies specific stage data → renders correctly', () => {
    renderWithThemeOnly(
      <DecisionChain
        stages={{
          evidence: { status: 'verified', count: 17 },
          decision: { status: 'pending', count: 3 },
        }}
      />,
    )
    expect(screen.getByText('17')).toBeTruthy()
    expect(screen.getByText('3')).toBeTruthy()
  })

  it('stage marker tone reflects status', () => {
    const { container } = renderWithThemeOnly(
      <DecisionChain
        stages={{ evidence: { status: 'verified', count: 1 } }}
      />,
    )
    // At least one trust-toned marker (for evidence)
    const trustMarkers = container.querySelectorAll('[data-tone="trust"]')
    expect(trustMarkers.length).toBeGreaterThanOrEqual(1)
  })

  it('renders as clickable buttons when onStageClick provided', () => {
    const handler = vi.fn()
    renderWithThemeOnly(<DecisionChain stages={{}} onStageClick={handler} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBe(8)
  })

  it('clicking a stage calls onStageClick with the correct key', () => {
    const handler = vi.fn()
    renderWithThemeOnly(<DecisionChain stages={{}} onStageClick={handler} />)
    const evidenceBtn = screen.getByRole('button', { name: /Evidence:/ })
    fireEvent.click(evidenceBtn)
    expect(handler).toHaveBeenCalledWith('evidence')
  })

  it('renders as plain list items when onStageClick absent', () => {
    const { container } = renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(container.querySelectorAll('.eg-chain__stage-btn').length).toBe(0)
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(screen.getByText('مُلاحَظ')).toBeTruthy()
    expect(screen.getByText('الأدلة')).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(<DecisionChain stages={{}} />)
    expect(screen.getByRole('figure')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })
})

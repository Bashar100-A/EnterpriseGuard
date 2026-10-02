import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { DecisionsPage } from './DecisionsPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('DecisionsPage', () => {
  it('renders the page title as h1', () => {
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(
      'Decision Intelligence',
    )
  })

  it('renders the description', () => {
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByText(/The full chain from observation to execution/i)).toBeTruthy()
  })

  it('renders the DecisionChain', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelector('[data-testid="eg-decision-chain"]')).not.toBeNull()
  })

  it('chain shows all three tiers', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelector('[data-tier="observed"]')).not.toBeNull()
    expect(container.querySelector('[data-tier="decided"]')).not.toBeNull()
    expect(container.querySelector('[data-tier="executed"]')).not.toBeNull()
  })

  it('chain shows all 8 stage labels', () => {
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByText('Evidence')).toBeTruthy()
    expect(screen.getByText('State')).toBeTruthy()
    expect(screen.getByText('Prediction')).toBeTruthy()
    expect(screen.getByText('Policy')).toBeTruthy()
    expect(screen.getByText('Decision')).toBeTruthy()
    expect(screen.getByText('Authority')).toBeTruthy()
    expect(screen.getByText('Manifest')).toBeTruthy()
    expect(screen.getByText('Outcome')).toBeTruthy()
  })

  it('renders the decisions table', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('table shows empty message', () => {
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByText('No decisions recorded in this scope')).toBeTruthy()
  })

  it('table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('renders the context strip', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelector('.eg-context')).not.toBeNull()
  })

  it('renders the assurance badge as Unknown', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('breadcrumb includes Intelligence group', () => {
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getAllByText('Intelligence').length).toBeGreaterThan(0)
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<DecisionsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(
      'استخبارات القرار',
    )
    await changeLanguage('en')
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })
})

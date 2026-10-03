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
  it('renders the title as h1', () => {
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
    expect(screen.getAllByText('Evidence').length).toBeGreaterThan(0)
    expect(screen.getAllByText('State').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Prediction').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Policy').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Decision').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Authority').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Manifest').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Outcome').length).toBeGreaterThan(0)
  })

  it('renders the RelationshipGraph', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelector('[data-testid="eg-relgraph"]')).not.toBeNull()
  })

  it('graph contains 8 nodes', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelectorAll('.eg-relgraph__node')).toHaveLength(8)
  })

  it('graph contains 7 edges', () => {
    const { container } = renderWithThemeOnly(<DecisionsPage />)
    expect(container.querySelectorAll('.eg-relgraph__edge')).toHaveLength(7)
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

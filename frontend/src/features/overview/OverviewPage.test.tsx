import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { OverviewPage } from './OverviewPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('OverviewPage', () => {
  it('renders the page title as h1', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Overview')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(
      screen.getByText('Sovereign Control Surface — operational overview'),
    ).toBeTruthy()
  })

  it('renders the doctrine strip with Observed / Decided / Executed', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByText('Observed')).toBeTruthy()
    expect(screen.getByText('Decided')).toBeTruthy()
    expect(screen.getByText('Executed')).toBeTruthy()
  })

  it('renders the context strip', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelector('.eg-context')).not.toBeNull()
    expect(screen.getByText('Environment')).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByText('System Health')).toBeTruthy()
    expect(screen.getByText('Active Evidence')).toBeTruthy()
    expect(screen.getByText('Pending Approvals')).toBeTruthy()
    expect(screen.getByText('Last Decision')).toBeTruthy()
  })

  it('metric values are — (no fabricated numbers)', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('shows Not Connected state indicator on metrics', () => {
    renderWithThemeOnly(<OverviewPage />)
    const nc = screen.getAllByText('Not Connected')
    expect(nc.length).toBeGreaterThanOrEqual(4)
  })

  it('renders two chart frames', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelectorAll('.eg-chartframe').length).toBe(2)
  })

  it('chart frames show their titles', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByText('Decision Volume')).toBeTruthy()
    expect(screen.getByText('Evidence Freshness')).toBeTruthy()
  })

  it('chart frames are in empty state (no fake charts)', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    const frames = container.querySelectorAll('.eg-chartframe')
    for (const f of Array.from(frames)) {
      expect(f.getAttribute('data-state')).toBe('empty')
    }
  })

  it('renders the enterprise activity table', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('activity table shows empty message', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByText('No recent activity in this scope')).toBeTruthy()
  })

  it('activity table does NOT render any rows', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('renders the assurance badge as Unknown', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    const badge = container.querySelector('.eg-workspace__assurance')
    expect(badge?.getAttribute('data-state')).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<OverviewPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('نظرة عامة')
    await changeLanguage('en')
  })

  it('has a doctrine strip with the ADIE invariant', () => {
    const { container } = renderWithThemeOnly(<OverviewPage />)
    expect(container.querySelector('.eg-overview__doctrine')).not.toBeNull()
    const seps = container.querySelectorAll('.eg-overview__doctrine-sep')
    expect(seps.length).toBe(2)
  })
})

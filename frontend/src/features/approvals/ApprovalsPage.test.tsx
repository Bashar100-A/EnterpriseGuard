import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ApprovalsPage } from './ApprovalsPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('ApprovalsPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Approvals')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByText(/Human-in-the-loop review/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByText('Pending Approvals')).toBeTruthy()
    expect(screen.getByText('Awaiting Authority')).toBeTruthy()
    expect(screen.getByText('Approved (24h)')).toBeTruthy()
    expect(screen.getByText('Rejected (24h)')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders two EnterpriseTables (queue + history)', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('queue table shows empty message', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByText('No pending approvals in this scope')).toBeTruthy()
  })

  it('history table shows empty message', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByText('No approval history in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Govern group', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getAllByText('Govern').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('does NOT contain any SeverityBadge (no fake severities)', () => {
    const { container } = renderWithThemeOnly(<ApprovalsPage />)
    expect(container.querySelector('.eg-badge--severity')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<ApprovalsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('الموافقات')
    await changeLanguage('en')
  })
})

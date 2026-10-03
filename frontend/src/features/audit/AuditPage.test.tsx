import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { AuditPage } from './AuditPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('AuditPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Audit')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByText(/The immutable trail/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByText('Total Events')).toBeTruthy()
    expect(screen.getByText('Distinct Actors')).toBeTruthy()
    expect(screen.getByText('Authorities Used')).toBeTruthy()
    expect(screen.getByText('Last Event')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders the filters panel', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getAllByText('Filter').length).toBeGreaterThan(0)
  })

  it('renders four filter rows', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(container.querySelectorAll('.eg-audit__filter-item').length).toBe(4)
  })

  it('renders all four filter labels', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByText('Actor')).toBeTruthy()
    expect(screen.getByText('Action')).toBeTruthy()
    expect(screen.getByText('Authority')).toBeTruthy()
    expect(screen.getByText('Time Window')).toBeTruthy()
  })

  it('Apply filter button is disabled', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByTestId('eg-audit-apply').hasAttribute('disabled')).toBe(true)
  })

  it('Clear filter button is disabled', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByTestId('eg-audit-clear').hasAttribute('disabled')).toBe(true)
  })

  it('renders the Timeline (empty state)', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByTestId('eg-timeline-empty')).toBeTruthy()
  })

  it('renders the reference section', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByText('Reference Format')).toBeTruthy()
  })

  it('reference section mentions Who, What, When, Why, Authority, Result, Reference', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(
      screen.getByText(/Who, What, When, Why, Authority, Result, Reference/i),
    ).toBeTruthy()
  })

  it('renders the audit trail table', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('trail table shows empty message', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByText('No audit events in this scope')).toBeTruthy()
  })

  it('trail table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Assurance group', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getAllByText('Assurance').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByText(/The UI never writes to the audit trail/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<AuditPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<AuditPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('التدقيق')
    await changeLanguage('en')
  })
})

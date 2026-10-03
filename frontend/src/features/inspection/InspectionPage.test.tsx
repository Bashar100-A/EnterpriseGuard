import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { InspectionPage } from './InspectionPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('InspectionPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Inspection')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByText(/On-demand system inspection/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByText('Scope Items')).toBeTruthy()
    expect(screen.getByText('Last Run')).toBeTruthy()
    expect(screen.getByText('Passed')).toBeTruthy()
    expect(screen.getByText('Failed')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders six scope items', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(container.querySelectorAll('.eg-inspection__scope-item').length).toBe(6)
  })

  it('renders all scope labels', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByText('Code')).toBeTruthy()
    expect(screen.getByText('Dependencies')).toBeTruthy()
    expect(screen.getByText('Configuration')).toBeTruthy()
    expect(screen.getByText('Tests')).toBeTruthy()
    expect(screen.getByText('Integrity')).toBeTruthy()
    expect(screen.getByText('Runtime')).toBeTruthy()
  })

  it('renders the Run Inspection button', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByTestId('eg-inspection-run')).toBeTruthy()
  })

  it('Run button is disabled (no fake backend)', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByTestId('eg-inspection-run').hasAttribute('disabled')).toBe(true)
  })

  it('Run button has an explanatory title', () => {
    renderWithThemeOnly(<InspectionPage />)
    const btn = screen.getByTestId('eg-inspection-run')
    expect(btn.getAttribute('title')).toMatch(/not connected/i)
  })

  it('renders the history table', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('history table shows empty message', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByText('No inspection runs in this scope')).toBeTruthy()
  })

  it('history table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Operate group', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getAllByText('Operate').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByText(/Run button remains disabled/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<InspectionPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<InspectionPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('الفحص')
    await changeLanguage('en')
  })
})

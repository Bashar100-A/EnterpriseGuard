import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ManifestsPage } from './ManifestsPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('ManifestsPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Execution Manifests')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByText(/What was planned for execution/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByText('Active Manifests')).toBeTruthy()
    expect(screen.getByText('Awaiting Execution')).toBeTruthy()
    expect(screen.getByText('Executed (24h)')).toBeTruthy()
    expect(screen.getByText('Failed (24h)')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders two EnterpriseTables (manifests + executions)', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('manifests table shows empty message', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByText('No manifests in this scope')).toBeTruthy()
  })

  it('executions table shows empty message', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByText('No executions recorded in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Govern group', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getAllByText('Govern').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByText(/A manifest is a plan/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<ManifestsPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<ManifestsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('بيانات التنفيذ')
    await changeLanguage('en')
  })
})

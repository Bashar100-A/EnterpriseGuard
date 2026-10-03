import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { AnalyticsPage } from './AnalyticsPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('AnalyticsPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Analytics')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByText(/Time series, dimensions, and comparative metrics/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels (using getAllByText)', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getAllByText('Data Points').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Dimensions').length).toBeGreaterThan(0)
    expect(screen.getByText('Active Windows')).toBeTruthy()
    expect(screen.getByText('Refresh Rate')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders three chart frames', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelectorAll('.eg-chartframe').length).toBe(3)
  })

  it('chart frames show titles', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByText('Event Volume')).toBeTruthy()
    expect(screen.getByText('Decision Latency')).toBeTruthy()
    expect(screen.getByText('Evidence Coverage')).toBeTruthy()
  })

  it('chart frames are empty (no fake charts)', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    const frames = container.querySelectorAll('.eg-chartframe')
    for (const f of Array.from(frames)) {
      expect(f.getAttribute('data-state')).toBe('empty')
    }
  })

  it('renders the Heatmap', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByTestId('eg-heatmap')).toBeTruthy()
  })

  it('Heatmap shows the empty hint (no data)', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByTestId('eg-heatmap-empty-hint')).toBeTruthy()
  })

  it('Heatmap renders 168 cells (7 × 24)', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelectorAll('.eg-heatmap__cell')).toHaveLength(168)
  })

  it('renders five dimension chips', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelectorAll('.eg-analytics__dimension-item').length).toBe(5)
  })

  it('renders all dimension labels', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByText('Time')).toBeTruthy()
    expect(screen.getByText('Source')).toBeTruthy()
    expect(screen.getByText('Severity')).toBeTruthy()
    expect(screen.getByText('Scope')).toBeTruthy()
    expect(screen.getByText('Authority')).toBeTruthy()
  })

  it('renders the snapshots table', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('snapshots table shows empty message', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByText('No analytics snapshots in this scope')).toBeTruthy()
  })

  it('snapshots table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelectorAll('.eg-table tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Assurance group', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getAllByText('Assurance').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByText(/Charts render in the empty state/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<AnalyticsPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<AnalyticsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('التحليلات')
    await changeLanguage('en')
  })
})

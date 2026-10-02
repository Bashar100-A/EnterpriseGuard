import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ChartFrame } from './ChartFrame'
import type { ChartState } from './ChartFrame'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('ChartFrame', () => {
  it('renders the title as an h3', () => {
    renderWithThemeOnly(
      <ChartFrame title="Latency over time" state="ready"><div>x</div></ChartFrame>,
    )
    expect(screen.getByRole('heading', { level: 3 }).textContent).toBe('Latency over time')
  })

  it('sets data-state attribute', () => {
    const { container } = renderWithThemeOnly(
      <ChartFrame title="x" state="stale"><div>c</div></ChartFrame>,
    )
    expect(container.querySelector('[data-state="stale"]')).not.toBeNull()
  })

  it('renders children only when state=ready', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="ready"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.getByText('the-chart')).toBeTruthy()
  })

  it('renders children when state=partial', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="partial"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.getByText('the-chart')).toBeTruthy()
  })

  it('does NOT render children when state=loading', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="loading"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.queryByText('the-chart')).toBeNull()
    expect(screen.getByText(/Loading chart/i)).toBeTruthy()
  })

  it('does NOT render children when state=empty', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="empty"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.queryByText('the-chart')).toBeNull()
    expect(screen.getByText(/No chart data available/i)).toBeTruthy()
  })

  it('does NOT render children when state=error', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="error"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.queryByText('the-chart')).toBeNull()
    expect(screen.getByText(/Could not load chart/i)).toBeTruthy()
  })

  it('does NOT render children when state=stale', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="stale"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.queryByText('the-chart')).toBeNull()
    expect(screen.getByText('Chart data is stale')).toBeTruthy()
  })

  it('does NOT render children when state=unavailable', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="unavailable"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.queryByText('the-chart')).toBeNull()
  })

  it('does NOT render children when state=permissionDenied', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="permissionDenied"><div>the-chart</div></ChartFrame>,
    )
    expect(screen.queryByText('the-chart')).toBeNull()
    expect(screen.getByText(/Permission denied/i)).toBeTruthy()
  })

  it('renders a partial banner only in partial state', () => {
    const { container } = renderWithThemeOnly(
      <ChartFrame title="x" state="partial"><div>c</div></ChartFrame>,
    )
    expect(container.querySelector('.eg-chartframe__banner')).not.toBeNull()
  })

  it('does NOT render partial banner in ready state', () => {
    const { container } = renderWithThemeOnly(
      <ChartFrame title="x" state="ready"><div>c</div></ChartFrame>,
    )
    expect(container.querySelector('.eg-chartframe__banner')).toBeNull()
  })

  it('shows retry button only in error state', () => {
    const handler = vi.fn()
    renderWithThemeOnly(
      <ChartFrame title="x" state="error" onRetry={handler}><div>c</div></ChartFrame>,
    )
    const btn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(btn)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does NOT show retry in non-error states even with onRetry', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="empty" onRetry={() => {}}><div>c</div></ChartFrame>,
    )
    expect(screen.queryByRole('button', { name: /Retry/i })).toBeNull()
  })

  it('renders expand button', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="ready"><div>c</div></ChartFrame>,
    )
    expect(screen.getByRole('button', { name: /Expand/i })).toBeTruthy()
  })

  it('toggles expanded state on expand click', () => {
    const { container } = renderWithThemeOnly(
      <ChartFrame title="x" state="ready"><div>c</div></ChartFrame>,
    )
    expect(container.querySelector('.eg-chartframe--expanded')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /Expand/i }))
    expect(container.querySelector('.eg-chartframe--expanded')).not.toBeNull()
    expect(screen.getByRole('button', { name: /Collapse/i })).toBeTruthy()
  })

  it('renders subtitle when provided', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="ready" subtitle="Last 7 days"><div>c</div></ChartFrame>,
    )
    expect(screen.getByText('Last 7 days')).toBeTruthy()
  })

  it('renders actions slot when provided', () => {
    renderWithThemeOnly(
      <ChartFrame
        title="x"
        state="ready"
        actions={<button type="button">Export</button>}
      ><div>c</div></ChartFrame>,
    )
    expect(screen.getByRole('button', { name: 'Export' })).toBeTruthy()
  })

  it('renders timestamp when provided', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="ready" timestamp="2026-10-02 22:00 UTC"><div>c</div></ChartFrame>,
    )
    expect(screen.getByText('2026-10-02 22:00 UTC')).toBeTruthy()
  })

  it('renders a StateIndicator with the translated state label', () => {
    renderWithThemeOnly(
      <ChartFrame title="x" state="ready"><div>c</div></ChartFrame>,
    )
    expect(screen.getByText('Ready')).toBeTruthy()
  })

  it('all 8 states render without crashing', () => {
    const all: ChartState[] = [
      'loading', 'ready', 'empty', 'partial', 'stale',
      'error', 'unavailable', 'permissionDenied',
    ]
    for (const s of all) {
      const { container } = renderWithThemeOnly(
        <ChartFrame title="x" state={s}><div>c</div></ChartFrame>,
      )
      expect(container.querySelector(`[data-state="${s}"]`)).not.toBeNull()
      cleanup()
    }
  })

  it('applies custom height to the chart body', () => {
    const { container } = renderWithThemeOnly(
      <ChartFrame title="x" state="ready" height={400}><div>c</div></ChartFrame>,
    )
    const body = container.querySelector('.eg-chartframe__body') as HTMLElement | null
    expect(body?.style.minHeight).toBe('400px')
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(
      <ChartFrame title="رسم" state="empty"><div>c</div></ChartFrame>,
    )
    expect(screen.getByText(/لا توجد بيانات للرسم/)).toBeTruthy()
    await changeLanguage('en')
  })
})

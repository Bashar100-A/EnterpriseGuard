import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { Heatmap } from './Heatmap'
import type { HeatmapCell } from './Heatmap'

function makeCells(): HeatmapCell[] {
  return [
    { day: 1, hour: 9, count: 2 },   // Mon 09:00 — low
    { day: 1, hour: 10, count: 15 }, // Mon 10:00 — medium
    { day: 2, hour: 14, count: 42 }, // Tue 14:00 — high
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('Heatmap', () => {
  it('renders a region with the default aria-label', () => {
    renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(screen.getByRole('region', { name: 'Activity density' })).toBeTruthy()
  })

  it('accepts a custom aria-label', () => {
    renderWithThemeOnly(<Heatmap cells={[]} ariaLabel="Custom heatmap" />)
    expect(screen.getByRole('region', { name: 'Custom heatmap' })).toBeTruthy()
  })

  it('renders 7 row headers (one per day)', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(container.querySelectorAll('.eg-heatmap__day')).toHaveLength(7)
  })

  it('renders 24 column headers (one per hour)', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(container.querySelectorAll('.eg-heatmap__hour')).toHaveLength(24)
  })

  it('renders 7 × 24 = 168 cells', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(container.querySelectorAll('.eg-heatmap__cell')).toHaveLength(168)
  })

  it('all cells are intensity=none when no data', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} />)
    const cells = container.querySelectorAll('.eg-heatmap__cell')
    for (const cell of Array.from(cells)) {
      expect(cell.getAttribute('data-intensity')).toBe('none')
    }
  })

  it('shows the empty hint when there is no data', () => {
    renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(screen.getByTestId('eg-heatmap-empty-hint')).toBeTruthy()
  })

  it('hides the empty hint when there is data', () => {
    renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    expect(screen.queryByTestId('eg-heatmap-empty-hint')).toBeNull()
  })

  it('classifies low counts (<5) as intensity=low', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    const cell = container.querySelector('[data-day="1"][data-hour="9"]')
    expect(cell?.getAttribute('data-intensity')).toBe('low')
  })

  it('classifies medium counts (5..19) as intensity=medium', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    const cell = container.querySelector('[data-day="1"][data-hour="10"]')
    expect(cell?.getAttribute('data-intensity')).toBe('medium')
  })

  it('classifies high counts (>=20) as intensity=high', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    const cell = container.querySelector('[data-day="2"][data-hour="14"]')
    expect(cell?.getAttribute('data-intensity')).toBe('high')
  })

  it('stores the raw count in data-count', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    const cell = container.querySelector('[data-day="2"][data-hour="14"]')
    expect(cell?.getAttribute('data-count')).toBe('42')
  })

  it('does NOT set data-count for null cells', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    const emptyCell = container.querySelector('[data-day="0"][data-hour="0"]')
    expect(emptyCell?.getAttribute('data-count')).toBeNull()
  })

  it('cells with count=0 are classified as intensity=none', () => {
    const cells: HeatmapCell[] = [{ day: 0, hour: 0, count: 0 }]
    const { container } = renderWithThemeOnly(<Heatmap cells={cells} />)
    const cell = container.querySelector('[data-day="0"][data-hour="0"]')
    expect(cell?.getAttribute('data-intensity')).toBe('none')
  })

  it('renders the intensity legend by default', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(container.querySelector('.eg-heatmap__legend')).not.toBeNull()
  })

  it('hides the legend when showLegend=false', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} showLegend={false} />)
    expect(container.querySelector('.eg-heatmap__legend')).toBeNull()
  })

  it('renders day names', () => {
    renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(screen.getByText('Sun')).toBeTruthy()
    expect(screen.getByText('Mon')).toBeTruthy()
    expect(screen.getByText('Sat')).toBeTruthy()
  })

  it('each cell has an aria-label', () => {
    const { container } = renderWithThemeOnly(<Heatmap cells={[]} />)
    const cells = container.querySelectorAll('.eg-heatmap__cell')
    for (const cell of Array.from(cells)) {
      expect(cell.getAttribute('aria-label')).toBeTruthy()
    }
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<Heatmap cells={[]} />)
    expect(screen.getByRole('region', { name: 'كثافة النشاط' })).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(<Heatmap cells={makeCells()} />)
    expect(screen.getByTestId('eg-heatmap')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })
})

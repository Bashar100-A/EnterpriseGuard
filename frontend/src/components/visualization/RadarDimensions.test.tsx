import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { RadarDimensions } from './RadarDimensions'
import type { RadarDimension } from './RadarDimensions'

function makeDimensions(): RadarDimension[] {
  return [
    { id: 'uptime',       label: 'Uptime',        score: 99, tone: 'trust' },
    { id: 'availability', label: 'Availability',  score: 95, tone: 'trust' },
    { id: 'latency',      label: 'Latency',       score: 72, tone: 'info' },
    { id: 'errorRate',    label: 'Error Rate',    score: 88, tone: 'trust' },
    { id: 'throughput',   label: 'Throughput',    score: 60, tone: 'warning' },
    { id: 'saturation',   label: 'Saturation',    score: null, tone: 'unknown' },
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('RadarDimensions', () => {
  it('renders an empty placeholder when dimensions=[]', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={[]} />)
    expect(screen.getByTestId('eg-radar-empty')).toBeTruthy()
    expect(screen.queryByTestId('eg-radar')).toBeNull()
  })

  it('empty placeholder shows the translated message', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={[]} />)
    expect(screen.getByText(/No dimension data to display/i)).toBeTruthy()
  })

  it('renders a region with the default aria-label', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    expect(screen.getByRole('region', { name: 'Multidimensional view' })).toBeTruthy()
  })

  it('accepts a custom aria-label', () => {
    renderWithThemeOnly(
      <RadarDimensions dimensions={makeDimensions()} ariaLabel="System radar" />,
    )
    expect(screen.getByRole('region', { name: 'System radar' })).toBeTruthy()
  })

  it('renders the SVG with role=img', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    expect(screen.getByRole('img')).toBeTruthy()
  })

  it('renders one axis label per dimension', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    expect(screen.getByTestId('eg-radar-label-uptime')).toBeTruthy()
    expect(screen.getByTestId('eg-radar-label-availability')).toBeTruthy()
    expect(screen.getByTestId('eg-radar-label-latency')).toBeTruthy()
    expect(screen.getByTestId('eg-radar-label-errorRate')).toBeTruthy()
    expect(screen.getByTestId('eg-radar-label-throughput')).toBeTruthy()
    expect(screen.getByTestId('eg-radar-label-saturation')).toBeTruthy()
  })

  it('renders the guide rings', () => {
    const { container } = renderWithThemeOnly(
      <RadarDimensions dimensions={makeDimensions()} />,
    )
    expect(container.querySelectorAll('.eg-radar__ring')).toHaveLength(4)
  })

  it('renders one axis line per dimension', () => {
    const { container } = renderWithThemeOnly(
      <RadarDimensions dimensions={makeDimensions()} />,
    )
    expect(container.querySelectorAll('.eg-radar__axis')).toHaveLength(6)
  })

  it('renders the data polygon', () => {
    const { container } = renderWithThemeOnly(
      <RadarDimensions dimensions={makeDimensions()} />,
    )
    expect(container.querySelectorAll('.eg-radar__polygon')).toHaveLength(1)
  })

  it('renders one vertex dot per dimension', () => {
    const { container } = renderWithThemeOnly(
      <RadarDimensions dimensions={makeDimensions()} />,
    )
    expect(container.querySelectorAll('.eg-radar__vertex-group circle')).toHaveLength(6)
  })

  it('renders scores as "value/max" for known dimensions', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} max={100} />)
    expect(screen.getByTestId('eg-radar-score-uptime').textContent).toBe('99/100')
    expect(screen.getByTestId('eg-radar-score-throughput').textContent).toBe('60/100')
  })

  it('renders "Unavailable" for null-score dimensions', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    expect(screen.getByTestId('eg-radar-score-saturation').textContent).toBe('Unavailable')
  })

  it('uses a custom max in score display', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} max={200} />)
    expect(screen.getByTestId('eg-radar-score-uptime').textContent).toBe('99/200')
  })

  it('shows the dimension count in the header', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    expect(screen.getByText('Dimensions')).toBeTruthy()
    expect(screen.getByText('6')).toBeTruthy()
  })

  it('shows the average score of known dimensions', () => {
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    // (99+95+72+88+60)/5 = 82.8 → rounded to 83
    expect(screen.getByText('83')).toBeTruthy()
  })

  it('shows — for average when all scores are null', () => {
    const dims: RadarDimension[] = [
      { id: 'a', label: 'A', score: null },
      { id: 'b', label: 'B', score: null },
    ]
    renderWithThemeOnly(<RadarDimensions dimensions={dims} />)
    // The avg stat value should be —
    const stats = document.querySelectorAll('.eg-radar__stat-value')
    expect(stats[1]?.textContent).toBe('—')
  })

  it('uses unknown tone for the polygon when all dimensions are unknown', () => {
    const dims: RadarDimension[] = [
      { id: 'a', label: 'A', score: null, tone: 'unknown' },
      { id: 'b', label: 'B', score: null, tone: 'unknown' },
    ]
    const { container } = renderWithThemeOnly(<RadarDimensions dimensions={dims} />)
    const poly = container.querySelector('.eg-radar__polygon')
    expect(poly?.getAttribute('data-tone')).toBe('unknown')
  })

  it('uses critical tone when any dimension is critical', () => {
    const dims: RadarDimension[] = [
      { id: 'a', label: 'A', score: 10, tone: 'critical' },
      { id: 'b', label: 'B', score: 90, tone: 'trust' },
    ]
    const { container } = renderWithThemeOnly(<RadarDimensions dimensions={dims} />)
    expect(container.querySelector('.eg-radar__polygon')?.getAttribute('data-tone')).toBe('critical')
  })

  it('uses warning tone when worst is warning', () => {
    const dims: RadarDimension[] = [
      { id: 'a', label: 'A', score: 40, tone: 'warning' },
      { id: 'b', label: 'B', score: 90, tone: 'trust' },
    ]
    const { container } = renderWithThemeOnly(<RadarDimensions dimensions={dims} />)
    expect(container.querySelector('.eg-radar__polygon')?.getAttribute('data-tone')).toBe('warning')
  })

  it('sets data-dimensions count', () => {
    const { container } = renderWithThemeOnly(
      <RadarDimensions dimensions={makeDimensions()} />,
    )
    expect(container.querySelector('[data-dimensions]')?.getAttribute('data-dimensions')).toBe('6')
  })

  it('renders with 3 dimensions (triangle)', () => {
    const dims: RadarDimension[] = [
      { id: 'a', label: 'A', score: 50 },
      { id: 'b', label: 'B', score: 70 },
      { id: 'c', label: 'C', score: 30 },
    ]
    renderWithThemeOnly(<RadarDimensions dimensions={dims} />)
    expect(screen.getByTestId('eg-radar')).toBeTruthy()
  })

  it('renders with 1 dimension without crashing', () => {
    const dims: RadarDimension[] = [
      { id: 'a', label: 'Only', score: 50 },
    ]
    renderWithThemeOnly(<RadarDimensions dimensions={dims} />)
    expect(screen.getByTestId('eg-radar')).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<RadarDimensions dimensions={[]} />)
    expect(screen.getByText(/لا توجد بيانات أبعاد للعرض/)).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(<RadarDimensions dimensions={makeDimensions()} />)
    expect(screen.getByTestId('eg-radar')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })
})

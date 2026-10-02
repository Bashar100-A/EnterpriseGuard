import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { MetricCard } from './MetricCard'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('MetricCard', () => {
  it('renders the label', () => {
    renderWithThemeOnly(
      <MetricCard label="Latency" value={{ value: 42, unit: 'ms' }} />,
    )
    expect(screen.getByText('Latency')).toBeTruthy()
  })

  it('renders the numeric value', () => {
    renderWithThemeOnly(<MetricCard label="x" value={{ value: 42 }} />)
    expect(screen.getByText('42')).toBeTruthy()
  })

  it('renders the unit when provided', () => {
    renderWithThemeOnly(<MetricCard label="x" value={{ value: 42, unit: '%' }} />)
    expect(screen.getByText('%')).toBeTruthy()
  })

  it('renders preformatted value instead of numeric when provided', () => {
    renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 42, formatted: '42.00' }} />,
    )
    expect(screen.getByText('42.00')).toBeTruthy()
  })

  it('renders — when value.value is null and no formatted', () => {
    renderWithThemeOnly(<MetricCard label="x" value={{ value: null }} />)
    expect(screen.getByText('—')).toBeTruthy()
  })

  it('does NOT render a unit when value is missing', () => {
    renderWithThemeOnly(<MetricCard label="x" value={{ value: null, unit: '%' }} />)
    expect(screen.queryByText('%')).toBeNull()
  })

  it('defaults dataState to unknown and sets data-state', () => {
    const { container } = renderWithThemeOnly(<MetricCard label="x" value={{ value: 1 }} />)
    expect(container.querySelector('[data-state="unknown"]')).not.toBeNull()
  })

  it('dataState=live maps to tone=trust', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} dataState="live" />,
    )
    expect(container.querySelector('[data-state="live"]')).not.toBeNull()
    expect(container.querySelector('[data-tone="trust"]')).not.toBeNull()
  })

  it('dataState=stale maps to tone=warning', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} dataState="stale" />,
    )
    expect(container.querySelector('[data-tone="warning"]')).not.toBeNull()
  })

  it('dataState=notConnected maps to tone=unknown', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} dataState="notConnected" />,
    )
    expect(container.querySelector('[data-tone="unknown"]')).not.toBeNull()
  })

  it('renders a trend arrow when trend is up', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} trend="up" trendValue="+3%" />,
    )
    expect(container.querySelector('[data-trend="up"]')).not.toBeNull()
    expect(screen.getByText('+3%')).toBeTruthy()
  })

  it('does NOT render a trend when undefined', () => {
    const { container } = renderWithThemeOnly(<MetricCard label="x" value={{ value: 1 }} />)
    expect(container.querySelector('.eg-metric__trend')).toBeNull()
  })

  it('does NOT render a trend when trend=unknown', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} trend="unknown" />,
    )
    expect(container.querySelector('.eg-metric__trend')).toBeNull()
  })

  it('renders context when provided', () => {
    renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} context="Last 24 hours" />,
    )
    expect(screen.getByText('Last 24 hours')).toBeTruthy()
  })

  it('renders timestamp when provided', () => {
    renderWithThemeOnly(
      <MetricCard label="x" value={{ value: 1 }} timestamp="2026-10-02 22:00 UTC" />,
    )
    expect(screen.getByText('2026-10-02 22:00 UTC')).toBeTruthy()
  })

  it('renders a StateIndicator with translated dataState label', () => {
    renderWithThemeOnly(<MetricCard label="x" value={{ value: 1 }} dataState="live" />)
    expect(screen.getByText('Live')).toBeTruthy()
  })

  it('renders a state indicator even when value is missing', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="x" value={{ value: null }} dataState="notConnected" />,
    )
    expect(container.querySelector('.eg-indicator')).not.toBeNull()
    expect(screen.getByText('Not Connected')).toBeTruthy()
  })

  it('renders an action slot when provided', () => {
    renderWithThemeOnly(
      <MetricCard
        label="x"
        value={{ value: 1 }}
        action={<button type="button">Details</button>}
      />,
    )
    expect(screen.getByRole('button', { name: 'Details' })).toBeTruthy()
  })

  it('uses the label as aria-label on the article', () => {
    const { container } = renderWithThemeOnly(
      <MetricCard label="Latency P99" value={{ value: 1 }} />,
    )
    expect(container.querySelector('article[aria-label="Latency P99"]')).not.toBeNull()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(
      <MetricCard label="زمن الاستجابة" value={{ value: 1 }} dataState="live" />,
    )
    expect(screen.getByText('حيّ')).toBeTruthy()
    await changeLanguage('en')
  })
})

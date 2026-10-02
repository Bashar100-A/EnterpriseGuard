import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { DataState } from './DataState'
import type { DataStateValue } from './DataState'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('DataState', () => {
  it('renders children when state is loaded', () => {
    renderWithThemeOnly(
      <DataState state="loaded"><div>actual-data</div></DataState>,
    )
    expect(screen.getByText('actual-data')).toBeTruthy()
  })

  it('does NOT render a placeholder when loaded', () => {
    const { container } = renderWithThemeOnly(
      <DataState state="loaded"><div>actual-data</div></DataState>,
    )
    expect(container.querySelector('.eg-datastate__placeholder')).toBeNull()
  })

  it('renders a loading placeholder when state is loading', () => {
    renderWithThemeOnly(<DataState state="loading"><div>x</div></DataState>)
    expect(screen.getByText(/Loading/i)).toBeTruthy()
    expect(screen.queryByText('x')).toBeNull()
  })

  it('renders an empty placeholder when state is empty', () => {
    renderWithThemeOnly(<DataState state="empty"><div>x</div></DataState>)
    expect(screen.getByText(/No data available/i)).toBeTruthy()
  })

  it('renders a partial banner AND children when state is partial', () => {
    renderWithThemeOnly(
      <DataState state="partial"><div>partial-content</div></DataState>,
    )
    expect(screen.getByText(/Partial data/i)).toBeTruthy()
    expect(screen.getByText('partial-content')).toBeTruthy()
  })

  it('renders a stale placeholder when state is stale', () => {
    renderWithThemeOnly(<DataState state="stale"><div>x</div></DataState>)
    expect(screen.getByText(/Data is stale/i)).toBeTruthy()
  })

  it('renders an unknown placeholder when state is unknown', () => {
    renderWithThemeOnly(<DataState state="unknown"><div>x</div></DataState>)
    expect(screen.getByText(/Insufficient evidence/i)).toBeTruthy()
  })

  it('renders an error placeholder when state is error', () => {
    renderWithThemeOnly(<DataState state="error"><div>x</div></DataState>)
    expect(screen.getByText(/Could not load/i)).toBeTruthy()
  })

  it('renders an unavailable placeholder when state is unavailable', () => {
    renderWithThemeOnly(<DataState state="unavailable"><div>x</div></DataState>)
    expect(screen.getByText(/Unavailable/i)).toBeTruthy()
  })

  it('renders a permissionDenied placeholder when state is permissionDenied', () => {
    renderWithThemeOnly(<DataState state="permissionDenied"><div>x</div></DataState>)
    expect(screen.getByText(/Permission denied/i)).toBeTruthy()
  })

  it('shows Retry only in error state', () => {
    const handler = vi.fn()
    renderWithThemeOnly(
      <DataState state="error" onRetry={handler}><div>x</div></DataState>,
    )
    const btn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(btn)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does NOT show Retry in non-error states', () => {
    renderWithThemeOnly(
      <DataState state="unknown" onRetry={() => {}}><div>x</div></DataState>,
    )
    expect(screen.queryByRole('button', { name: /Retry/i })).toBeNull()
  })

  it('sets data-state for test targeting', () => {
    const { container } = renderWithThemeOnly(<DataState state="empty"><div>x</div></DataState>)
    expect(container.querySelector('[data-state="empty"]')).not.toBeNull()
  })

  it('accepts a custom message override for non-loaded states', () => {
    renderWithThemeOnly(
      <DataState state="unknown" message="Custom message"><div>x</div></DataState>,
    )
    expect(screen.getByText('Custom message')).toBeTruthy()
  })

  it('renders all 9 states without crashing', () => {
    const all: DataStateValue[] = [
      'loading', 'loaded', 'empty', 'partial', 'stale',
      'unknown', 'error', 'unavailable', 'permissionDenied',
    ]
    for (const s of all) {
      const { container } = renderWithThemeOnly(
        <DataState state={s}><div>c</div></DataState>,
      )
      expect(container.querySelector(`[data-state="${s}"]`)).not.toBeNull()
      cleanup()
    }
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<DataState state="unknown"><div>x</div></DataState>)
    expect(screen.getByText(/غير معروف/)).toBeTruthy()
    await changeLanguage('en')
  })
})

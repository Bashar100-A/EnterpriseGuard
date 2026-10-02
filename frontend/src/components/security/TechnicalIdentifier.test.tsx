import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest'
import { screen, cleanup, fireEvent, waitFor } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { TechnicalIdentifier } from './TechnicalIdentifier'

beforeEach(() => {
  // Provide a clipboard mock that resolves successfully by default.
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: {
      writeText: vi.fn().mockResolvedValue(undefined),
    },
  })
})

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('TechnicalIdentifier', () => {
  it('renders the full value when short', () => {
    renderWithThemeOnly(<TechnicalIdentifier value="SHORT-ID" />)
    expect(screen.getByText('SHORT-ID')).toBeTruthy()
  })

  it('does NOT truncate when mode=none', () => {
    const long = 'abcdefghijklmnopqrstuvwxyz0123456789'
    renderWithThemeOnly(<TechnicalIdentifier value={long} truncate="none" />)
    expect(screen.getByText(long)).toBeTruthy()
  })

  it('truncates in the middle by default for long values', () => {
    const long = 'abcdefghijklmnopqrstuvwxyz0123456789'
    renderWithThemeOnly(<TechnicalIdentifier value={long} maxLength={12} />)
    // Middle truncation: 6 chars + … + 5 chars
    const body = document.querySelector('.eg-tech-id__body')
    expect(body?.textContent).toContain('…')
    expect(body?.textContent?.length).toBe(12)
  })

  it('truncate=start adds ellipsis at the beginning', () => {
    renderWithThemeOnly(
      <TechnicalIdentifier value="abcdefghijklmnop" truncate="start" maxLength={8} />,
    )
    const body = document.querySelector('.eg-tech-id__body')
    expect(body?.textContent?.startsWith('…')).toBe(true)
  })

  it('truncate=end adds ellipsis at the end', () => {
    renderWithThemeOnly(
      <TechnicalIdentifier value="abcdefghijklmnop" truncate="end" maxLength={8} />,
    )
    const body = document.querySelector('.eg-tech-id__body')
    expect(body?.textContent?.endsWith('…')).toBe(true)
  })

  it('sets title to the full value by default', () => {
    const long = 'abcdefghijklmnopqrstuvwxyz0123456789'
    const { container } = renderWithThemeOnly(<TechnicalIdentifier value={long} />)
    const val = container.querySelector('[title]')
    expect(val?.getAttribute('title')).toBe(long)
  })

  it('accepts a custom title', () => {
    const { container } = renderWithThemeOnly(
      <TechnicalIdentifier value="x" title="Custom tooltip" />,
    )
    expect(container.querySelector('[title="Custom tooltip"]')).not.toBeNull()
  })

  it('sets dir="ltr" on the value even in RTL document', () => {
    document.documentElement.dir = 'rtl'
    const { container } = renderWithThemeOnly(<TechnicalIdentifier value="dec-1" />)
    const val = container.querySelector('.eg-tech-id__value')
    expect(val?.getAttribute('dir')).toBe('ltr')
    document.documentElement.dir = 'ltr'
  })

  it('renders prefix when provided', () => {
    renderWithThemeOnly(<TechnicalIdentifier value="12345" prefix="DEC-" />)
    expect(screen.getByText('DEC-')).toBeTruthy()
    expect(screen.getByText('12345')).toBeTruthy()
  })

  it('renders label when provided', () => {
    renderWithThemeOnly(<TechnicalIdentifier value="x" label="Decision ID" />)
    expect(screen.getByText('Decision ID')).toBeTruthy()
  })

  it('renders a copy button by default', () => {
    renderWithThemeOnly(<TechnicalIdentifier value="x" />)
    expect(screen.getByRole('button', { name: /Copy identifier/i })).toBeTruthy()
  })

  it('does NOT render a copy button when copyable=false', () => {
    renderWithThemeOnly(<TechnicalIdentifier value="x" copyable={false} />)
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('calls clipboard.writeText with the FULL value on copy', async () => {
    const long = 'abcdefghijklmnopqrstuvwxyz0123456789'
    renderWithThemeOnly(<TechnicalIdentifier value={long} maxLength={8} />)
    fireEvent.click(screen.getByRole('button', { name: /Copy identifier/i }))
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(long)
    })
  })

  it('shows Copied state after successful copy', async () => {
    renderWithThemeOnly(<TechnicalIdentifier value="x" />)
    fireEvent.click(screen.getByRole('button', { name: /Copy identifier/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Copied/i })).toBeTruthy()
    })
  })

  it('shows Copy failed when clipboard rejects', async () => {
    ;(navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('denied'),
    )
    renderWithThemeOnly(<TechnicalIdentifier value="x" />)
    fireEvent.click(screen.getByRole('button', { name: /Copy identifier/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Copy failed/i })).toBeTruthy()
    })
  })

  it('renders in size=sm with correct data class', () => {
    const { container } = renderWithThemeOnly(<TechnicalIdentifier value="x" size="sm" />)
    expect(container.querySelector('.eg-tech-id--sm')).not.toBeNull()
  })

  it('renders in size=md by default', () => {
    const { container } = renderWithThemeOnly(<TechnicalIdentifier value="x" />)
    expect(container.querySelector('.eg-tech-id--md')).not.toBeNull()
  })
})

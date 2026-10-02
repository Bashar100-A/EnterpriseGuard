import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { AssuranceRail } from './AssuranceRail'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('AssuranceRail', () => {
  it('renders with role=complementary', () => {
    renderWithProviders(<AssuranceRail />)
    const rail = screen.getByRole('complementary')
    expect(rail).toBeTruthy()
  })

  it('renders the title', () => {
    renderWithProviders(<AssuranceRail />)
    expect(screen.getByText('Assurance')).toBeTruthy()
  })

  it('renders all six section titles', () => {
    renderWithProviders(<AssuranceRail />)
    expect(screen.getByText('System State')).toBeTruthy()
    expect(screen.getByText('Data Freshness')).toBeTruthy()
    expect(screen.getByText('Evidence State')).toBeTruthy()
    expect(screen.getByText('Verification')).toBeTruthy()
    expect(screen.getByText('Permissions')).toBeTruthy()
    expect(screen.getByText('Audit Reference')).toBeTruthy()
  })

  it('defaults unknown sections to Unknown state', () => {
    const { container } = renderWithProviders(<AssuranceRail />)
    const unknowns = container.querySelectorAll('[data-state="unknown"]')
    expect(unknowns.length).toBeGreaterThanOrEqual(4)
  })

  it('defaults permissions to notConnected', () => {
    const { container } = renderWithProviders(<AssuranceRail />)
    const el = container.querySelector('[data-state="notConnected"]')
    expect(el).not.toBeNull()
    expect(el?.textContent).toContain('Not Connected')
  })

  it('defaults auditReference to Unavailable', () => {
    renderWithProviders(<AssuranceRail />)
    expect(screen.getByText('Unavailable')).toBeTruthy()
  })

  it('accepts a verification state and renders translated value', () => {
    const { container } = renderWithProviders(<AssuranceRail verification="verified" />)
    const el = container.querySelector('[data-state="verified"]')
    expect(el?.textContent).toContain('Verified')
  })

  it('accepts a custom auditReference string', () => {
    renderWithProviders(<AssuranceRail auditReference="AUD-2026-0042" />)
    expect(screen.getByText('AUD-2026-0042')).toBeTruthy()
  })

  it('does NOT render close button when onClose is absent', () => {
    const { container } = renderWithProviders(<AssuranceRail />)
    expect(container.querySelector('.eg-assurance__close')).toBeNull()
  })

  it('renders close button and calls onClose when clicked', () => {
    const onClose = vi.fn()
    renderWithProviders(<AssuranceRail onClose={onClose} />)
    const btn = screen.getByRole('button', { name: /Close assurance panel/i })
    fireEvent.click(btn)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('renders in Arabic when language is ar', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithProviders(<AssuranceRail />)
    expect(screen.getByText('الضمان')).toBeTruthy()
    expect(screen.getByText('حالة النظام')).toBeTruthy()
    expect(screen.getByText('غير متصل')).toBeTruthy()
    await changeLanguage('en')
  })
})

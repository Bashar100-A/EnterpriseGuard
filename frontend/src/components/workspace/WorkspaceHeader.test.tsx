import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { WorkspaceHeader } from './WorkspaceHeader'
import { ContextStrip } from './ContextStrip'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  window.localStorage.clear()
})

describe('WorkspaceHeader', () => {
  it('renders the title as an h1', () => {
    renderWithProviders(<WorkspaceHeader title="Evidence Integrity" />)
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1.textContent).toBe('Evidence Integrity')
  })

  it('renders description when provided', () => {
    renderWithProviders(
      <WorkspaceHeader title="Title" description="Some description" />,
    )
    expect(screen.getByText('Some description')).toBeTruthy()
  })

  it('does not render description element when absent', () => {
    const { container } = renderWithProviders(<WorkspaceHeader title="Title" />)
    expect(container.querySelector('.eg-workspace__description')).toBeNull()
  })

  it('renders breadcrumb items with current mark', () => {
    renderWithProviders(
      <WorkspaceHeader
        title="Title"
        breadcrumb={[
          { label: 'Trust' },
          { label: 'Evidence', current: true },
        ]}
      />,
    )
    expect(screen.getByText('Trust')).toBeTruthy()
    const current = screen.getByText('Evidence')
    expect(current.getAttribute('aria-current')).toBe('page')
  })

  it('does not render breadcrumb when absent', () => {
    const { container } = renderWithProviders(<WorkspaceHeader title="Title" />)
    expect(container.querySelector('.eg-workspace__breadcrumb')).toBeNull()
  })

  it('renders actions slot when provided', () => {
    renderWithProviders(
      <WorkspaceHeader
        title="Title"
        actions={<button type="button">Filter</button>}
      />,
    )
    expect(screen.getByRole('button', { name: 'Filter' })).toBeTruthy()
  })

  it('renders assurance badge with data-state', () => {
    const { container } = renderWithProviders(
      <WorkspaceHeader title="Title" assuranceState="unknown" />,
    )
    const badge = container.querySelector('[data-state="unknown"]')
    expect(badge).not.toBeNull()
    expect(badge?.textContent).toBe('Unknown')
  })

  it('assurance badge has accessible label', () => {
    renderWithProviders(<WorkspaceHeader title="Title" assuranceState="verified" />)
    const badge = screen.getByLabelText(/Assurance: Verified/i)
    expect(badge).toBeTruthy()
  })

  it('renders context node when provided', () => {
    renderWithProviders(
      <WorkspaceHeader
        title="Title"
        context={<ContextStrip environment="Test" />}
      />,
    )
    expect(screen.getByText('Environment')).toBeTruthy()
    expect(screen.getByText('Test')).toBeTruthy()
  })
})

describe('ContextStrip', () => {
  it('renders all four labels', () => {
    renderWithProviders(<ContextStrip />)
    expect(screen.getByText('Environment')).toBeTruthy()
    expect(screen.getByText('Region')).toBeTruthy()
    expect(screen.getByText('Data Freshness')).toBeTruthy()
    expect(screen.getByText('Last Verification')).toBeTruthy()
  })

  it('defaults to Unknown when no values provided', () => {
    renderWithProviders(<ContextStrip />)
    const unknowns = screen.getAllByText('Unknown')
    expect(unknowns.length).toBeGreaterThanOrEqual(2)
  })

  it('renders provided values verbatim', () => {
    renderWithProviders(
      <ContextStrip environment="Production" region="EU-West" dataFreshness="Stale" lastVerification="2026-10-02" />,
    )
    expect(screen.getByText('Production')).toBeTruthy()
    expect(screen.getByText('EU-West')).toBeTruthy()
    expect(screen.getByText('Stale')).toBeTruthy()
    expect(screen.getByText('2026-10-02')).toBeTruthy()
  })

  it('has role=group with aria-label', () => {
    renderWithProviders(<ContextStrip />)
    const group = screen.getByRole('group', { name: /Context/i })
    expect(group).toBeTruthy()
  })
})

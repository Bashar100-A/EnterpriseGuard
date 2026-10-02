import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup, fireEvent, waitFor } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { GovernancePage } from './GovernancePage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('GovernancePage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Governance')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByText(/Policies, approvals, and the authority boundary/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<GovernancePage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getAllByText('Active Policies').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Pending Approvals').length).toBeGreaterThan(0)
    expect(screen.getByText('Approved (24h)')).toBeTruthy()
    expect(screen.getByText('Rejected (24h)')).toBeTruthy()
  })

  it('metric values are — (no fake data)', () => {
    const { container } = renderWithThemeOnly(<GovernancePage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders two EnterpriseTables (policies + approvals)', () => {
    const { container } = renderWithThemeOnly(<GovernancePage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('policies table shows empty message', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByText('No policies configured in this scope')).toBeTruthy()
  })

  it('approvals table shows empty message', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByText('No pending approvals in this scope')).toBeTruthy()
  })

  it('tables do NOT render fabricated rows', () => {
    const { container } = renderWithThemeOnly(<GovernancePage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Govern group', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getAllByText('Govern').length).toBeGreaterThan(0)
  })

  it('renders the Propose Policy action button', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByTestId('eg-governance-propose')).toBeTruthy()
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('dangerous dialog is NOT open by default', () => {
    const { container } = renderWithThemeOnly(<GovernancePage />)
    expect(container.querySelector('[data-testid="eg-danger-dialog"]')).toBeNull()
  })

  it('clicking Propose Policy opens the DangerousActionDialog', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => {
      expect(screen.getByTestId('eg-danger-dialog')).toBeTruthy()
    })
  })

  it('opened dialog shows the intent text', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => {
      expect(
        screen.getByText('Create a new policy in the current scope'),
      ).toBeTruthy()
    })
  })

  it('opened dialog requires acknowledgment', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => {
      expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(true)
    })
  })

  it('acknowledging enables the confirm button', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => {
      expect(screen.getByTestId('eg-danger-ack')).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId('eg-danger-ack'))
    await waitFor(() => {
      expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(false)
    })
  })

  it('clicking confirm closes the dialog (does NOT execute anything)', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => screen.getByTestId('eg-danger-ack'))
    fireEvent.click(screen.getByTestId('eg-danger-ack'))
    fireEvent.click(screen.getByTestId('eg-danger-confirm'))
    await waitFor(() => {
      expect(screen.queryByTestId('eg-danger-dialog')).toBeNull()
    })
  })

  it('dialog severity is high (data-severity)', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => {
      expect(
        screen.getByTestId('eg-danger-dialog').getAttribute('data-severity'),
      ).toBe('high')
    })
  })

  it('cancelling closes the dialog', async () => {
    renderWithThemeOnly(<GovernancePage />)
    fireEvent.click(screen.getByTestId('eg-governance-propose'))
    await waitFor(() => screen.getByTestId('eg-danger-cancel'))
    fireEvent.click(screen.getByTestId('eg-danger-cancel'))
    await waitFor(() => {
      expect(screen.queryByTestId('eg-danger-dialog')).toBeNull()
    })
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<GovernancePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('الحوكمة')
    await changeLanguage('en')
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<GovernancePage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })
})

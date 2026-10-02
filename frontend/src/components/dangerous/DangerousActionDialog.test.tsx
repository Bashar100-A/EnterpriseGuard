import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { DangerousActionDialog } from './DangerousActionDialog'

interface Props {
  severity?: 'elevated' | 'high' | 'critical'
  confirmPhrase?: string
  requireAcknowledgment?: boolean
}

function renderDialog(overrides: Props = {}, handlers: {
  onClose?: () => void
  onConfirm?: () => void
} = {}) {
  const onClose = handlers.onClose ?? vi.fn()
  const onConfirm = handlers.onConfirm ?? vi.fn()
  const props = {
    open: true,
    onClose,
    intent: 'Rollback to snapshot 42',
    explanation: 'A regression was detected after the last deployment.',
    impacts: [
      'Active sessions will be terminated.',
      'In-flight requests will be dropped.',
    ],
    requiredAuthority: 'Role: OPERATOR / Policy: POL-042',
    backendAuthority: 'ADIE authorization service',
    severity: overrides.severity ?? ('elevated' as const),
    confirmPhrase: overrides.confirmPhrase,
    requireAcknowledgment: overrides.requireAcknowledgment,
    onConfirm,
  }
  const utils = renderWithThemeOnly(<DangerousActionDialog {...props} />)
  return { ...utils, onClose, onConfirm }
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('DangerousActionDialog', () => {
  it('renders nothing when open=false', () => {
    const { container } = renderWithThemeOnly(
      <DangerousActionDialog
        open={false}
        onClose={() => {}}
        intent="x"
        explanation="y"
        impacts={[]}
        requiredAuthority="Role: X"
        backendAuthority="Backend"
        onConfirm={() => {}}
      />,
    )
    expect(container.querySelector('[data-testid="eg-danger-dialog"]')).toBeNull()
  })

  it('renders a dialog with role=alertdialog', () => {
    renderDialog()
    const dialog = screen.getByRole('alertdialog')
    expect(dialog).toBeTruthy()
  })

  it('has aria-modal=true', () => {
    renderDialog()
    expect(screen.getByRole('alertdialog').getAttribute('aria-modal')).toBe('true')
  })

  it('shows the intent', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-intent').textContent).toBe('Rollback to snapshot 42')
  })

  it('shows the explanation', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-explanation').textContent).toBe(
      'A regression was detected after the last deployment.',
    )
  })

  it('renders all impact items', () => {
    renderDialog()
    expect(screen.getByText('Active sessions will be terminated.')).toBeTruthy()
    expect(screen.getByText('In-flight requests will be dropped.')).toBeTruthy()
  })

  it('shows "no impacts" when impacts=[]', () => {
    renderWithThemeOnly(
      <DangerousActionDialog
        open
        onClose={() => {}}
        intent="x"
        explanation="y"
        impacts={[]}
        requiredAuthority="Role: X"
        backendAuthority="Backend"
        onConfirm={() => {}}
      />,
    )
    expect(screen.getByTestId('eg-danger-impact-list').textContent).toMatch(/No specific impacts/i)
  })

  it('shows the required authority', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-authority-required').textContent).toBe(
      'Role: OPERATOR / Policy: POL-042',
    )
  })

  it('shows the backend authority source', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-authority-backend').textContent).toBe(
      'ADIE authorization service',
    )
  })

  it('renders the backend authorization note', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-note').textContent).toMatch(/decides whether to authorize/i)
  })

  it('defaults severity to elevated', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-dialog').getAttribute('data-severity')).toBe('elevated')
  })

  it('severity=critical sets data-severity=critical and tone=critical', () => {
    renderDialog({ severity: 'critical' })
    const dialog = screen.getByTestId('eg-danger-dialog')
    expect(dialog.getAttribute('data-severity')).toBe('critical')
    expect(dialog.getAttribute('data-tone')).toBe('critical')
  })

  it('severity=high sets tone=warning', () => {
    renderDialog({ severity: 'high' })
    expect(screen.getByTestId('eg-danger-dialog').getAttribute('data-tone')).toBe('warning')
  })

  // ---- Acknowledgment flow ----

  it('confirm is disabled when acknowledgment required but unchecked', () => {
    renderDialog()
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(true)
  })

  it('checking acknowledgment enables confirm (no phrase required)', () => {
    renderDialog()
    fireEvent.click(screen.getByTestId('eg-danger-ack'))
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(false)
  })

  it('when requireAcknowledgment=false, confirm enabled without click', () => {
    renderDialog({ requireAcknowledgment: false })
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(false)
  })

  // ---- Phrase flow ----

  it('confirm disabled when phrase required but empty', () => {
    renderDialog({ confirmPhrase: 'ROLLBACK', requireAcknowledgment: false })
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(true)
  })

  it('confirm disabled when phrase does not match', () => {
    renderDialog({ confirmPhrase: 'ROLLBACK', requireAcknowledgment: false })
    fireEvent.change(screen.getByTestId('eg-danger-phrase'), {
      target: { value: 'rollback' },
    })
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(true)
  })

  it('shows mismatch error when phrase differs', () => {
    renderDialog({ confirmPhrase: 'ROLLBACK', requireAcknowledgment: false })
    fireEvent.change(screen.getByTestId('eg-danger-phrase'), {
      target: { value: 'wrong' },
    })
    expect(screen.getByText(/does not match/i)).toBeTruthy()
  })

  it('confirm enabled when phrase matches exactly', () => {
    renderDialog({ confirmPhrase: 'ROLLBACK', requireAcknowledgment: false })
    fireEvent.change(screen.getByTestId('eg-danger-phrase'), {
      target: { value: 'ROLLBACK' },
    })
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(false)
  })

  it('both ack and phrase required -> both must be satisfied', () => {
    renderDialog({ confirmPhrase: 'ROLLBACK' })
    // Only ack
    fireEvent.click(screen.getByTestId('eg-danger-ack'))
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(true)
    // Add phrase
    fireEvent.change(screen.getByTestId('eg-danger-phrase'), {
      target: { value: 'ROLLBACK' },
    })
    expect(screen.getByTestId('eg-danger-confirm').hasAttribute('disabled')).toBe(false)
  })

  // ---- Actions ----

  it('clicking Request calls onConfirm when enabled', () => {
    const { onConfirm } = renderDialog({ requireAcknowledgment: false })
    fireEvent.click(screen.getByTestId('eg-danger-confirm'))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('clicking Request when disabled does NOT call onConfirm', () => {
    const { onConfirm } = renderDialog()
    fireEvent.click(screen.getByTestId('eg-danger-confirm'))
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('clicking Cancel calls onClose', () => {
    const { onClose } = renderDialog()
    fireEvent.click(screen.getByTestId('eg-danger-cancel'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('clicking the X button calls onClose', () => {
    const { onClose } = renderDialog()
    // The X button and the Cancel button share the accessible name "Cancel"
    // (X uses aria-label="Cancel" while visually showing "×"). To target the
    // X specifically, use its dedicated class.
    const xBtn = document.querySelector('.eg-danger__close') as HTMLElement | null
    expect(xBtn).not.toBeNull()
    fireEvent.click(xBtn as HTMLElement)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('pressing Escape on the dialog calls onClose', () => {
    const { onClose } = renderDialog()
    fireEvent.keyDown(screen.getByTestId('eg-danger-dialog'), { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('clicking the backdrop calls onClose', () => {
    const { onClose } = renderDialog()
    const overlay = document.querySelector('.eg-danger-overlay') as HTMLElement | null
    fireEvent.click(overlay as HTMLElement)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  // ---- RTL / i18n ----

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderDialog({ requireAcknowledgment: false })
    expect(screen.getByRole('alertdialog').getAttribute('aria-label')).toBe('تأكيد إجراء خطِر')
    expect(screen.getByTestId('eg-danger-confirm').textContent).toBe('طلب التفويض')
    await changeLanguage('en')
  })

  it('renders without error in RTL document direction', () => {
    document.documentElement.dir = 'rtl'
    renderDialog({ requireAcknowledgment: false })
    expect(screen.getByTestId('eg-danger-dialog')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })

  it('does NOT execute anything by itself', () => {
    // Sanity: no matter what the user does, nothing runs until they click Request.
    const { onConfirm } = renderDialog({ confirmPhrase: 'ROLLBACK' })
    fireEvent.click(screen.getByTestId('eg-danger-ack'))
    fireEvent.change(screen.getByTestId('eg-danger-phrase'), {
      target: { value: 'ROLLBACK' },
    })
    // Still not clicked. Nothing should have fired.
    expect(onConfirm).not.toHaveBeenCalled()
  })
})

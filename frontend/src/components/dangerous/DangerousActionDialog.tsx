import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from '../security/tone'

export type DangerSeverity = 'elevated' | 'high' | 'critical'

const TONE_BY_SEVERITY: Record<DangerSeverity, SemanticTone> = {
  elevated: 'warning',
  high: 'warning',
  critical: 'critical',
}

export interface DangerousActionDialogProps {
  /** Whether the dialog is visible. Controlled by the parent. */
  open: boolean
  /** Called when the user dismisses the dialog (Cancel, Escape, backdrop, X). */
  onClose: () => void

  /** Short verb-phrase describing what will be requested, e.g. "Rollback to snapshot 42". */
  intent: string
  /** Human-readable explanation of why this is needed. */
  explanation: string
  /** List of concrete consequences. May be empty. */
  impacts: string[]

  /** The authority the caller is expected to hold (e.g., "Role: OPERATOR / POL-042"). */
  requiredAuthority: string
  /** Text describing the source of final authorization (e.g., "ADIE backend"). */
  backendAuthority: string

  /** Visual severity. Default: 'elevated'. */
  severity?: DangerSeverity | undefined

  /**
   * If set, the user must type this exact string to enable the confirm button.
   * Recommended for 'critical' actions. The match is case-sensitive by design.
   */
  confirmPhrase?: string | undefined

  /** If true, the user must check the acknowledgment box. Default: true. */
  requireAcknowledgment?: boolean | undefined

  /**
   * Invoked when the user completes all confirmations. The parent is
   * responsible for sending this intent to the backend.
   *
   * This dialog NEVER executes the action itself. It only signals intent.
   */
  onConfirm: () => void

  /** Optional extra content, rendered below the impact list. */
  extra?: ReactNode
}

/**
 * DangerousActionDialog — spec §25.
 *
 * The canonical confirmation surface for any operation with real
 * consequences. Enforces the ADIE flow:
 *
 *   Intent → Explanation → Impact → Required Authority
 *   → Confirmation → Backend Authorization
 *
 * Steps 6+ happen OUTSIDE this component. This dialog never executes,
 * never pretends to have executed, and never bypasses the backend.
 */
export function DangerousActionDialog({
  open,
  onClose,
  intent,
  explanation,
  impacts,
  requiredAuthority,
  backendAuthority,
  severity = 'elevated',
  confirmPhrase,
  requireAcknowledgment = true,
  onConfirm,
  extra,
}: DangerousActionDialogProps): ReactElement | null {
  const { t } = useTranslation('dangerous')
  const [ack, setAck] = useState(false)
  const [phrase, setPhrase] = useState('')
  const dialogRef = useRef<HTMLDivElement | null>(null)
  const initialFocusRef = useRef<HTMLButtonElement | null>(null)

  // Reset internal state every time the dialog opens.
  useEffect(() => {
    if (open) {
      setAck(false)
      setPhrase('')
    }
  }, [open])

  const tone = TONE_BY_SEVERITY[severity]
  const severityLabel = t(`severity.${severity}`) as string

  const ackSatisfied = !requireAcknowledgment || ack
  const phraseSatisfied = confirmPhrase === undefined || phrase === confirmPhrase
  const canConfirm = ackSatisfied && phraseSatisfied

  const blockedReason = !ackSatisfied
    ? (t('blocked.acknowledge') as string)
    : !phraseSatisfied
      ? (t('blocked.phrase') as string)
      : ''

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    },
    [onClose],
  )

  // Focus the cancel button on open (safer default than confirm).
  useEffect(() => {
    if (!open) return
    const el = initialFocusRef.current
    if (el === null) return
    const id = window.requestAnimationFrame(() => el.focus())
    return () => window.cancelAnimationFrame(id)
  }, [open])

  const impactItems = useMemo(
    () => impacts.map((text, i) => ({ key: i, text })),
    [impacts],
  )

  const handleConfirm = useCallback(() => {
    if (!canConfirm) return
    onConfirm()
  }, [canConfirm, onConfirm])

  if (!open) return null

  return (
    <div
      className="eg-danger-overlay"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-label={t('title') as string}
        aria-describedby="eg-danger-description"
        className="eg-danger"
        data-severity={severity}
        data-tone={tone}
        data-testid="eg-danger-dialog"
        onKeyDown={handleKeyDown}
      >
        <header className="eg-danger__header">
          <div className="eg-danger__heading">
            <span
              className="eg-danger__severity"
              data-tone={tone}
              data-testid="eg-danger-severity"
            >
              {severityLabel}
            </span>
            <h2 className="eg-danger__title" id="eg-danger-description">
              {t('title')}
            </h2>
          </div>
          <button
            type="button"
            className="eg-danger__close"
            onClick={onClose}
            aria-label={t('actions.cancel') as string}
            title={t('actions.cancel') as string}
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <div className="eg-danger__body">
          <section className="eg-danger__section">
            <div className="eg-danger__section-title">{t('sections.intent')}</div>
            <div className="eg-danger__section-body" data-testid="eg-danger-intent">
              {intent}
            </div>
          </section>

          <section className="eg-danger__section">
            <div className="eg-danger__section-title">{t('sections.explanation')}</div>
            <div className="eg-danger__section-body" data-testid="eg-danger-explanation">
              {explanation}
            </div>
          </section>

          <section className="eg-danger__section">
            <div className="eg-danger__section-title">{t('sections.impact')}</div>
            <div className="eg-danger__section-body">
              {impactItems.length === 0 ? (
                <div className="eg-danger__impact-empty" data-testid="eg-danger-impact-list">
                  {t('impacts.none')}
                </div>
              ) : (
                <ul className="eg-danger__impact-list" data-testid="eg-danger-impact-list">
                  {impactItems.map((it) => (
                    <li key={it.key} className="eg-danger__impact-item">
                      {it.text}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className="eg-danger__section">
            <div className="eg-danger__section-title">{t('sections.authorityRequired')}</div>
            <div className="eg-danger__section-body eg-mono" data-testid="eg-danger-authority-required">
              {requiredAuthority}
            </div>
          </section>

          <section className="eg-danger__section">
            <div className="eg-danger__section-title">{t('sections.authorityBackend')}</div>
            <div className="eg-danger__section-body" data-testid="eg-danger-authority-backend">
              {backendAuthority}
            </div>
          </section>

          {extra !== undefined && (
            <section className="eg-danger__section">{extra}</section>
          )}

          <section className="eg-danger__section">
            <div className="eg-danger__section-title">{t('sections.confirmation')}</div>

            {requireAcknowledgment && (
              <label className="eg-danger__ack" data-testid="eg-danger-ack-wrap">
                <input
                  type="checkbox"
                  checked={ack}
                  onChange={(e) => setAck(e.target.checked)}
                  data-testid="eg-danger-ack"
                />
                <span>{t('acknowledgment.label')}</span>
              </label>
            )}

            {confirmPhrase !== undefined && (
              <div className="eg-danger__phrase" data-testid="eg-danger-phrase-wrap">
                <div className="eg-danger__phrase-instruction">
                  {t('phrase.instruction', { phrase: confirmPhrase })}
                </div>
                <input
                  type="text"
                  className="eg-danger__phrase-input eg-mono"
                  value={phrase}
                  onChange={(e) => setPhrase(e.target.value)}
                  placeholder={t('phrase.placeholder') as string}
                  dir="ltr"
                  autoComplete="off"
                  spellCheck={false}
                  data-testid="eg-danger-phrase"
                />
                {phrase !== '' && phrase !== confirmPhrase && (
                  <div className="eg-danger__phrase-error" role="alert">
                    {t('phrase.mismatch')}
                  </div>
                )}
              </div>
            )}
          </section>

          <p className="eg-danger__note" data-testid="eg-danger-note">
            {t('note.backend')}
          </p>
        </div>

        <footer className="eg-danger__footer">
          <button
            ref={initialFocusRef}
            type="button"
            className="eg-danger__btn eg-danger__btn--cancel"
            onClick={onClose}
            data-testid="eg-danger-cancel"
          >
            {t('actions.cancel')}
          </button>
          <button
            type="button"
            className="eg-danger__btn eg-danger__btn--confirm"
            onClick={handleConfirm}
            disabled={!canConfirm}
            title={canConfirm ? undefined : blockedReason}
            data-testid="eg-danger-confirm"
            data-disabled={!canConfirm ? 'true' : undefined}
          >
            {t('actions.request')}
          </button>
        </footer>
      </div>
    </div>
  )
}

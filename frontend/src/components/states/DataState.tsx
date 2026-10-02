import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export type DataStateValue =
  | 'loading'
  | 'loaded'
  | 'empty'
  | 'partial'
  | 'stale'
  | 'unknown'
  | 'error'
  | 'unavailable'
  | 'permissionDenied'

export interface DataStateProps {
  state: DataStateValue
  children?: ReactNode
  /** Called when the user clicks Retry (only shown in error state). */
  onRetry?: (() => void) | undefined
  /** Optional custom retry label. */
  retryLabel?: ReactNode
  /** Optional custom message for any state. */
  message?: ReactNode
}

interface PlaceholderProps {
  title: string
  message: string
  onRetry?: (() => void) | undefined
  retryLabel?: ReactNode
  tone?: 'neutral' | 'warning' | 'critical'
}

function Placeholder({
  title,
  message,
  onRetry,
  retryLabel,
  tone = 'neutral',
}: PlaceholderProps): ReactElement {
  return (
    <div className="eg-datastate__placeholder" data-tone={tone} role="status">
      <div className="eg-datastate__title">{title}</div>
      <div className="eg-datastate__message">{message}</div>
      {onRetry !== undefined && (
        <button type="button" className="eg-datastate__action" onClick={onRetry}>
          {retryLabel ?? 'Retry'}
        </button>
      )}
    </div>
  )
}

/**
 * DataState — honest wrapper for content that may or may not be available.
 *
 * When state === 'loaded' or 'partial', children are rendered (partial
 * additionally renders a small banner). All other states replace children
 * with a clear placeholder so the UI never pretends data is present.
 *
 * No fake data. No silent fallbacks. No misleading "Healthy".
 */
export function DataState({
  state,
  children,
  onRetry,
  retryLabel,
  message,
}: DataStateProps): ReactElement {
  const { t } = useTranslation('states')

  if (state === 'loaded') {
    return (
      <div className="eg-datastate" data-state="loaded">
        {children}
      </div>
    )
  }

  if (state === 'partial') {
    return (
      <div className="eg-datastate" data-state="partial">
        <div className="eg-datastate__banner" role="note">
          <span className="eg-datastate__banner-title">
            {t('dataState.partial.title')}
          </span>
          <span className="eg-datastate__banner-message">
            {message ?? t('dataState.partial.message')}
          </span>
        </div>
        {children}
      </div>
    )
  }

  const title = t(`dataState.${state}.title`) as string
  const msg = message ?? (t(`dataState.${state}.message`) as string)

  let tone: PlaceholderProps['tone'] = 'neutral'
  if (state === 'error') {
    tone = 'critical'
  } else if (state === 'stale' || state === 'unavailable') {
    tone = 'warning'
  }

  return (
    <div className="eg-datastate" data-state={state}>
      <Placeholder
        title={title}
        message={typeof msg === 'string' ? msg : ''}
        onRetry={state === 'error' ? onRetry : undefined}
        retryLabel={retryLabel}
        tone={tone}
      />
    </div>
  )
}

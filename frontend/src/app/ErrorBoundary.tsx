import { Component, type ErrorInfo, type ReactElement, type ReactNode } from 'react'
import i18n from '../i18n'

export interface ErrorBoundaryProps {
  children: ReactNode
  /** Optional callback for logging / diagnostics. */
  onError?: (error: Error, info: ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  /** Short reference code safe to show users (no stack traces). */
  reference: string
}

function makeReference(): string {
  const y = new Date().getUTCFullYear()
  const rand = Math.floor(Math.random() * 0xffff).toString(16).padStart(4, '0')
  return `UI-ERR-${y}-${rand}`
}

/**
 * ErrorBoundary — spec §23.
 * Never renders stack traces, file paths, or internal exceptions in production.
 * Shows a safe message + a reference code + Retry button.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = { hasError: false, reference: '' }

  public static getDerivedStateFromError(): Partial<ErrorBoundaryState> {
    return { hasError: true, reference: makeReference() }
  }

  public componentDidCatch(error: Error, info: ErrorInfo): void {
    // Safe logging via callback only. Never echo to console in production
    // unless the host app decides to.
    this.props.onError?.(error, info)
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false, reference: '' })
  }

  public render(): ReactElement | ReactNode {
    if (!this.state.hasError) return this.props.children

    const t = i18n.getFixedT(null, 'errors')
    return (
      <div className="eg-boundary" role="alert">
        <h2 className="eg-boundary__title">{t('boundary.title')}</h2>
        <p className="eg-boundary__message">{t('boundary.message')}</p>
        <p className="eg-boundary__reference">
          <span className="eg-boundary__reference-label">{t('boundary.reference')}:</span>{' '}
          <span className="eg-mono">{this.state.reference}</span>
        </p>
        <button type="button" className="eg-boundary__retry" onClick={this.handleRetry}>
          {t('boundary.retry')}
        </button>
      </div>
    )
  }
}

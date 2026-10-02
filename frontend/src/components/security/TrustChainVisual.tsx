import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { TechnicalIdentifier } from './TechnicalIdentifier'

export interface TrustChainVisualProps {
  /** Merkle root hash (40+ chars) or null when unavailable. */
  root: string | null
  /** Chain height in blocks/checkpoints. null when unknown. */
  height: number | null
  /** Optional compact rendering. */
  compact?: boolean
}

/**
 * TrustChainVisual — a cinematic visualization of the SIBB Merkle chain.
 *
 * Renders a horizontal sequence of "leaves" that visually converge into a
 * single root. When root is null, the visualization collapses to a single
 * honest "not established" placeholder.
 *
 * No fabrication. No animation that pretends progress.
 */
export function TrustChainVisual({
  root,
  height,
  compact = false,
}: TrustChainVisualProps): ReactElement {
  const { t } = useTranslation('sibb')

  const leafCount = compact ? 5 : 7
  const hasRoot = root !== null
  const hasHeight = height !== null && height > 0

  return (
    <div
      className={`eg-trust-chain ${compact ? 'eg-trust-chain--compact' : ''}`}
      data-testid="eg-trust-chain"
      data-state={hasRoot ? 'ready' : 'unknown'}
      role="img"
      aria-label={t('merkle.title') as string}
    >
      <div className="eg-trust-chain__leaves" aria-hidden="true">
        {Array.from({ length: leafCount }).map((_, i) => (
          <span
            key={i}
            className="eg-trust-chain__leaf"
            data-empty={hasRoot ? 'false' : 'true'}
          />
        ))}
      </div>

      <div className="eg-trust-chain__convergence" aria-hidden="true">
        {Array.from({ length: leafCount }).map((_, i) => (
          <span key={i} className="eg-trust-chain__branch" />
        ))}
      </div>

      <div className="eg-trust-chain__root-wrap">
        <div className="eg-trust-chain__root" data-empty={hasRoot ? 'false' : 'true'}>
          {hasRoot ? (
            <TechnicalIdentifier value={root} maxLength={20} copyable={!compact} />
          ) : (
            <span className="eg-trust-chain__root-empty">
              {t('merkle.rootUnavailable')}
            </span>
          )}
        </div>
        <div className="eg-trust-chain__root-caption">
          {t('merkle.rootCaption')}
          {hasHeight && (
            <>
              <span className="eg-trust-chain__sep">·</span>
              <span className="eg-trust-chain__height">
                {t('metrics.chainHeight')}: {height}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

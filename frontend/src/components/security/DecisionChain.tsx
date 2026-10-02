import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { toneForStatus, type StatusKey } from './tone'

export type ChainStageKey =
  | 'evidence'
  | 'state'
  | 'prediction'
  | 'policy'
  | 'decision'
  | 'authority'
  | 'manifest'
  | 'outcome'

export type ChainTier = 'observed' | 'decided' | 'executed'

export interface ChainStage {
  /** Semantic status shown as a dot + label. */
  status: StatusKey
  /** Item count for this stage. null when unknown. */
  count: number | null
}

export interface DecisionChainProps {
  /** Stage → data. Missing stages default to unknown + null count. */
  stages: Partial<Record<ChainStageKey, ChainStage>>
  /** Optional handler when a stage is clicked. */
  onStageClick?: (key: ChainStageKey) => void
}

const TIER_ORDER: ChainTier[] = ['observed', 'decided', 'executed']

const STAGES_BY_TIER: Record<ChainTier, ChainStageKey[]> = {
  observed: ['evidence', 'state', 'prediction'],
  decided: ['policy', 'decision', 'authority'],
  executed: ['manifest', 'outcome'],
}

function defaultStage(): ChainStage {
  return { status: 'unknown', count: null }
}

/**
 * DecisionChain — the canonical ADIE pipeline visualization.
 *
 * Spec §38 (RelationshipGraph foundation).
 *
 * Renders three tiers side by side, each containing its stages in order:
 *
 *   OBSERVED  →   DECIDED   →   EXECUTED
 *   Evidence      Policy        Manifest
 *   State         Decision      Outcome
 *   Prediction    Authority
 *
 * Each stage shows:
 *   - A semantic dot (tone from status)
 *   - Its translated label
 *   - A count (or — when unavailable)
 *
 * The chain does NOT calculate anything. It does NOT decide. It only
 * visualizes the pipeline. Stages that were not supplied render as
 * unknown with a null count.
 */
export function DecisionChain({
  stages,
  onStageClick,
}: DecisionChainProps): ReactElement {
  const { t } = useTranslation('decisions')

  const renderStage = (key: ChainStageKey): ReactElement => {
    const stage = stages[key] ?? defaultStage()
    const tone = toneForStatus(stage.status)
    const label = t(`chain.stage.${key}`) as string
    const description = t(`chain.stageDescription.${key}`) as string
    const countText = stage.count === null ? '—' : String(stage.count)
    const clickable = onStageClick !== undefined

    const content = (
      <>
        <span className="eg-chain__stage-marker" data-tone={tone} aria-hidden="true" />
        <span className="eg-chain__stage-label">{label}</span>
        <span className="eg-chain__stage-count" title={countText}>
          {countText}
        </span>
      </>
    )

    if (clickable) {
      return (
        <li key={key} className="eg-chain__stage eg-chain__stage--clickable">
          <button
            type="button"
            className="eg-chain__stage-btn"
            onClick={() => onStageClick(key)}
            title={description}
            aria-label={`${label}: ${description}`}
          >
            {content}
          </button>
        </li>
      )
    }

    return (
      <li key={key} className="eg-chain__stage" title={description}>
        {content}
      </li>
    )
  }

  return (
    <div
      className="eg-chain"
      role="figure"
      aria-label={t('chain.label') as string}
      data-testid="eg-decision-chain"
    >
      {TIER_ORDER.map((tier, i) => (
        <div key={tier} className="eg-chain__segment">
          {i > 0 && (
            <span
              className="eg-chain__connector"
              aria-label={t('chain.arrowLabel') as string}
            >
              <span aria-hidden="true">→</span>
            </span>
          )}
          <div
            className={`eg-chain__tier eg-chain__tier--${tier}`}
            data-tier={tier}
            data-testid={`eg-chain-tier-${tier}`}
          >
            <div className="eg-chain__tier-header">
              {t(`chain.tier.${tier}`)}
            </div>
            <ul className="eg-chain__stages" role="list">
              {STAGES_BY_TIER[tier].map(renderStage)}
            </ul>
          </div>
        </div>
      ))}
    </div>
  )
}

// Components
export { StatusBadge } from './StatusBadge'
export type { StatusBadgeProps } from './StatusBadge'

export { SeverityBadge } from './SeverityBadge'
export type { SeverityBadgeProps } from './SeverityBadge'

export { StateIndicator } from './StateIndicator'
export type { StateIndicatorProps } from './StateIndicator'

export { VerificationBadge } from './VerificationBadge'
export type { VerificationBadgeProps } from './VerificationBadge'

export { EnvironmentBadge } from './EnvironmentBadge'
export type { EnvironmentBadgeProps } from './EnvironmentBadge'

export { EvidenceIndicator } from './EvidenceIndicator'
export type { EvidenceIndicatorProps } from './EvidenceIndicator'

export { TechnicalIdentifier } from './TechnicalIdentifier'
export type { TechnicalIdentifierProps, TruncateMode } from './TechnicalIdentifier'

export { TrustChainVisual } from './TrustChainVisual'
export type { TrustChainVisualProps } from './TrustChainVisual'

export { DecisionChain } from './DecisionChain'
export type { DecisionChainProps, ChainStage, ChainStageKey, ChainTier } from './DecisionChain'

// Types and helpers
export { SEMANTIC_TONES, ENVIRONMENT_KEYS, isEnvironmentKey } from './tone'
export {
  toneForStatus,
  toneForSeverity,
  toneForVerification,
} from './tone'
export type {
  SemanticTone,
  StatusKey,
  SeverityLevel,
  VerificationState,
  EnvironmentKey,
} from './tone'

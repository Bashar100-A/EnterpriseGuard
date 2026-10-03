export {
  NotConnectedError,
  requireLiveClient,
  UNAVAILABLE_CONTEXT,
} from './types'
export type { AdapterContext, AdapterMode } from './types'

export { createEvidenceAdapter } from './evidence.adapter'
export type { EvidenceAdapter } from './evidence.adapter'

export { createDecisionAdapter } from './decision.adapter'
export type { DecisionAdapter } from './decision.adapter'

export { createManifestAdapter } from './manifest.adapter'
export type { ManifestAdapter } from './manifest.adapter'

export { createPolicyAdapter } from './policy.adapter'
export type { PolicyAdapter } from './policy.adapter'

export { createAuditAdapter } from './audit.adapter'
export type { AuditAdapter } from './audit.adapter'

import type { AdapterContext } from './types'
import { createEvidenceAdapter, type EvidenceAdapter } from './evidence.adapter'
import { createDecisionAdapter, type DecisionAdapter } from './decision.adapter'
import { createManifestAdapter, type ManifestAdapter } from './manifest.adapter'
import { createPolicyAdapter, type PolicyAdapter } from './policy.adapter'
import { createAuditAdapter, type AuditAdapter } from './audit.adapter'

export interface Adapters {
  evidence: EvidenceAdapter
  decision: DecisionAdapter
  manifest: ManifestAdapter
  policy: PolicyAdapter
  audit: AuditAdapter
}

export function createAdapters(ctx: AdapterContext): Adapters {
  return {
    evidence: createEvidenceAdapter(ctx),
    decision: createDecisionAdapter(ctx),
    manifest: createManifestAdapter(ctx),
    policy: createPolicyAdapter(ctx),
    audit: createAuditAdapter(ctx),
  }
}

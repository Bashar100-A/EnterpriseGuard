/**
 * UI-01.J.4 — Typed query key factories.
 *
 * Rules:
 *   - Every key is a readonly tuple for TanStack Query compatibility.
 *   - Keys are hierarchical: ['domain', 'kind', ...args].
 *   - Factories are pure and deterministic.
 */

import type {
  AuditListRequest,
  DecisionListRequest,
  EvidenceListRequest,
  ManifestListRequest,
  PolicyListRequest,
} from '../contracts'

export const queryKeys = {
  evidence: {
    all: ['evidence'] as const,
    list: (req: EvidenceListRequest) =>
      ['evidence', 'list', req] as const,
    detail: (id: string) => ['evidence', 'detail', id] as const,
  },
  decision: {
    all: ['decision'] as const,
    list: (req: DecisionListRequest) =>
      ['decision', 'list', req] as const,
    detail: (id: string) => ['decision', 'detail', id] as const,
  },
  manifest: {
    all: ['manifest'] as const,
    list: (req: ManifestListRequest) =>
      ['manifest', 'list', req] as const,
    detail: (id: string) => ['manifest', 'detail', id] as const,
  },
  policy: {
    all: ['policy'] as const,
    list: (req: PolicyListRequest) =>
      ['policy', 'list', req] as const,
    detail: (id: string) => ['policy', 'detail', id] as const,
  },
  audit: {
    all: ['audit'] as const,
    list: (req: AuditListRequest) =>
      ['audit', 'list', req] as const,
  },
} as const

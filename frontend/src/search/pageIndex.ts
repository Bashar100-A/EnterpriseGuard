/**
 * Page metadata used for fuzzy search over the entire application.
 * Every route maps to its i18n namespace (which holds title + description)
 * and a set of English keywords that help with query matching.
 *
 * Keywords are deliberately in English only; Fuse.js operates on the
 * English label + description + keyword list, so cross-language search
 * works through the translated title/description fields.
 */
export interface PageRef {
  path: string
  namespace: string
  keywords: string[]
}

export const PAGES: PageRef[] = [
  { path: '/',              namespace: 'overview',    keywords: ['home', 'dashboard', 'situation', 'doctrine'] },
  { path: '/operations',    namespace: 'operations',  keywords: ['incidents', 'queue', 'soc', 'response'] },
  { path: '/intelligence',  namespace: 'threat',      keywords: ['threats', 'iocs', 'feeds', 'adversary'] },
  { path: '/decisions',     namespace: 'decisions',   keywords: ['decision', 'chain', 'pipeline', 'authority'] },
  { path: '/evidence',      namespace: 'evidence',    keywords: ['evidence', 'verified', 'provenance', 'integrity'] },
  { path: '/provenance',    namespace: 'provenance',  keywords: ['source', 'origin', 'trace', 'chain'] },
  { path: '/sibb',          namespace: 'sibb',        keywords: ['trust', 'merkle', 'baseline', 'signature', 'checkpoint'] },
  { path: '/policies',      namespace: 'policies',    keywords: ['policy', 'rules', 'version', 'catalog'] },
  { path: '/governance',    namespace: 'governance',  keywords: ['governance', 'policy', 'approval', 'authority'] },
  { path: '/approvals',     namespace: 'approvals',   keywords: ['approve', 'review', 'human', 'queue'] },
  { path: '/manifests',     namespace: 'manifests',   keywords: ['manifest', 'execution', 'plan', 'outcome'] },
  { path: '/health',        namespace: 'health',      keywords: ['health', 'services', 'uptime', 'latency'] },
  { path: '/inspection',    namespace: 'inspection',  keywords: ['inspect', 'scan', 'audit', 'code'] },
  { path: '/maintenance',   namespace: 'maintenance', keywords: ['maintenance', 'rollback', 'change', 'window'] },
  { path: '/analytics',     namespace: 'analytics',   keywords: ['analytics', 'charts', 'trends', 'dimensions'] },
  { path: '/reports',       namespace: 'reports',     keywords: ['reports', 'export', 'schedule', 'delivery'] },
  { path: '/audit',         namespace: 'audit',       keywords: ['audit', 'trail', 'log', 'who', 'when'] },
  { path: '/access',        namespace: 'access',      keywords: ['users', 'roles', 'permissions', 'identity'] },
  { path: '/settings',      namespace: 'config',      keywords: ['config', 'settings', 'flags', 'environment'] },
]

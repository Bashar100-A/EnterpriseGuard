/**
 * UI-01.J.4 — QueryClient factory.
 *
 * Design notes (ADIE):
 *   - NotConnectedError is a terminal state, not a transient one.
 *     Retrying it wastes cycles and confuses the UI. It must not retry.
 *   - Mutations never auto-retry (they may trigger side effects).
 *   - refetchOnWindowFocus is disabled: analyst attention is intentional.
 */

import { QueryClient } from '@tanstack/react-query'
import { NotConnectedError } from '../adapters'

const DEFAULT_STALE_MS = 30_000
const MAX_QUERY_RETRIES = 2

export interface CreateQueryClientOptions {
  staleTimeMs?: number
  maxRetries?: number
}

export function createQueryClient(
  opts: CreateQueryClientOptions = {},
): QueryClient {
  const staleTime = opts.staleTimeMs ?? DEFAULT_STALE_MS
  const maxRetries = opts.maxRetries ?? MAX_QUERY_RETRIES

  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          if (error instanceof NotConnectedError) return false
          return failureCount < maxRetries
        },
      },
      mutations: {
        retry: false,
      },
    },
  })
}

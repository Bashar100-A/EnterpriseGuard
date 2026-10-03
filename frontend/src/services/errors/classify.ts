import { ApiClientError } from '../api'
import { NotConnectedError } from '../adapters'
import type {
  ClassifiedError,
  ErrorKind,
  SuggestedAction,
} from './types'

const KIND_TO_KEY: Record<ErrorKind, string> = {
  network: 'api.network',
  timeout: 'api.timeout',
  auth: 'api.auth',
  validation: 'api.validation',
  'not-found': 'api.notFound',
  server: 'api.server',
  'not-connected': 'connection.notConnected',
  unknown: 'unknown.generic',
}

const KIND_TO_ACTION: Record<ErrorKind, SuggestedAction> = {
  network: 'retry',
  timeout: 'retry',
  auth: 'reauthenticate',
  validation: 'fix-input',
  'not-found': 'navigate-back',
  server: 'wait-and-retry',
  'not-connected': 'connect-backend',
  unknown: 'contact-admin',
}

function build(
  kind: ErrorKind,
  status: number | null,
  requestId: string | null,
  raw: unknown,
): ClassifiedError {
  return {
    kind,
    key: KIND_TO_KEY[kind],
    action: KIND_TO_ACTION[kind],
    status,
    requestId,
    raw,
  }
}

export function classifyError(err: unknown): ClassifiedError {
  if (err instanceof NotConnectedError) {
    return build('not-connected', null, null, err)
  }

  if (err instanceof ApiClientError) {
    if (err.kind === 'auth') return build('auth', err.status, err.requestId ?? null, err)
    if (err.kind === 'network') return build('network', err.status, err.requestId ?? null, err)
    if (err.kind === 'timeout') return build('timeout', err.status, err.requestId ?? null, err)
    if (err.kind === 'validation') return build('validation', err.status, err.requestId ?? null, err)
    if (err.kind === 'notFound') return build('not-found', err.status, err.requestId ?? null, err)
    if (err.kind === 'server') return build('server', err.status, err.requestId ?? null, err)
    return build('unknown', err.status, err.requestId ?? null, err)
  }

  return build('unknown', null, null, err)
}

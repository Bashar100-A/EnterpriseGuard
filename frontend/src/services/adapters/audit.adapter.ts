import type {
  AuditListRequest,
  AuditListResponse,
} from '../contracts'
import { requireLiveClient, type AdapterContext } from './types'

export interface AuditAdapter {
  list(req: AuditListRequest): Promise<AuditListResponse>
}

const BASE = '/v1/audit'

export function createAuditAdapter(ctx: AdapterContext): AuditAdapter {
  return {
    async list(req) {
      const client = requireLiveClient(ctx, 'audit.list')
      return client.post<AuditListResponse>(`${BASE}/list`, req)
    },
  }
}

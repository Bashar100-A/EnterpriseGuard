import type {
  PolicyDetailResponse,
  PolicyListRequest,
  PolicyListResponse,
} from '../contracts'
import { requireLiveClient, type AdapterContext } from './types'

export interface PolicyAdapter {
  list(req: PolicyListRequest): Promise<PolicyListResponse>
  detail(id: string): Promise<PolicyDetailResponse>
}

const BASE = '/v1/policies'

export function createPolicyAdapter(ctx: AdapterContext): PolicyAdapter {
  return {
    async list(req) {
      const client = requireLiveClient(ctx, 'policy.list')
      return client.post<PolicyListResponse>(`${BASE}/list`, req)
    },
    async detail(id) {
      const client = requireLiveClient(ctx, 'policy.detail')
      return client.get<PolicyDetailResponse>(`${BASE}/${encodeURIComponent(id)}`)
    },
  }
}

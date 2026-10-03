import type {
  DecisionDetailResponse,
  DecisionListRequest,
  DecisionListResponse,
} from '../contracts'
import { requireLiveClient, type AdapterContext } from './types'

export interface DecisionAdapter {
  list(req: DecisionListRequest): Promise<DecisionListResponse>
  detail(id: string): Promise<DecisionDetailResponse>
}

const BASE = '/v1/decisions'

export function createDecisionAdapter(ctx: AdapterContext): DecisionAdapter {
  return {
    async list(req) {
      const client = requireLiveClient(ctx, 'decision.list')
      return client.post<DecisionListResponse>(`${BASE}/list`, req)
    },
    async detail(id) {
      const client = requireLiveClient(ctx, 'decision.detail')
      return client.get<DecisionDetailResponse>(`${BASE}/${encodeURIComponent(id)}`)
    },
  }
}

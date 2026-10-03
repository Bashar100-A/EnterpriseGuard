import type {
  EvidenceDetailResponse,
  EvidenceListRequest,
  EvidenceListResponse,
} from '../contracts'
import { requireLiveClient, type AdapterContext } from './types'

export interface EvidenceAdapter {
  list(req: EvidenceListRequest): Promise<EvidenceListResponse>
  detail(id: string): Promise<EvidenceDetailResponse>
}

const BASE = '/v1/evidence'

export function createEvidenceAdapter(ctx: AdapterContext): EvidenceAdapter {
  return {
    async list(req) {
      const client = requireLiveClient(ctx, 'evidence.list')
      return client.post<EvidenceListResponse>(`${BASE}/list`, req)
    },
    async detail(id) {
      const client = requireLiveClient(ctx, 'evidence.detail')
      return client.get<EvidenceDetailResponse>(`${BASE}/${encodeURIComponent(id)}`)
    },
  }
}

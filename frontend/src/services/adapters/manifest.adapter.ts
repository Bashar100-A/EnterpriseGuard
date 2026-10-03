import type {
  ManifestDetailResponse,
  ManifestListRequest,
  ManifestListResponse,
} from '../contracts'
import { requireLiveClient, type AdapterContext } from './types'

export interface ManifestAdapter {
  list(req: ManifestListRequest): Promise<ManifestListResponse>
  detail(id: string): Promise<ManifestDetailResponse>
}

const BASE = '/v1/manifests'

export function createManifestAdapter(ctx: AdapterContext): ManifestAdapter {
  return {
    async list(req) {
      const client = requireLiveClient(ctx, 'manifest.list')
      return client.post<ManifestListResponse>(`${BASE}/list`, req)
    },
    async detail(id) {
      const client = requireLiveClient(ctx, 'manifest.detail')
      return client.get<ManifestDetailResponse>(`${BASE}/${encodeURIComponent(id)}`)
    },
  }
}

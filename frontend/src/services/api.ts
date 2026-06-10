import type { LineageResponse, ImpactResponse, LineageDirection } from '../types/graph';

const API_BASE_URL = '/api/v1';

async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}

export interface SearchResult {
  id: string;
  type: string;
  description?: string;
  owner?: string;
  system?: string;
}

export const api = {
  /** Test connection to Neo4j */
  testConnection: () => fetchApi<{ neo4j_status: string }>('/lineage/test'),

  /** Load demo graph data */
  seedGraph: () => fetchApi<{ status: string }>('/lineage/seed'),

  /** Get lineage for a node */
  getLineage: (nodeId: string, direction: LineageDirection = 'both', depth: number = 10) =>
    fetchApi<LineageResponse>(`/lineage/${encodeURIComponent(nodeId)}?direction=${direction}&depth=${depth}`),

  /** Get upstream lineage */
  getUpstreamLineage: (nodeId: string, depth: number = 10) =>
    fetchApi<LineageResponse>(`/lineage/upstream/${encodeURIComponent(nodeId)}?depth=${depth}`),

  /** Get downstream lineage */
  getDownstreamLineage: (nodeId: string, depth: number = 10) =>
    fetchApi<LineageResponse>(`/lineage/downstream/${encodeURIComponent(nodeId)}?depth=${depth}`),

  /** Get impact analysis */
  getImpactAnalysis: (nodeId: string, depth: number = 10) =>
    fetchApi<ImpactResponse>(`/lineage/impact/${encodeURIComponent(nodeId)}?depth=${depth}`),

  /** Validate graph health */
  validateGraph: () => fetchApi<{ is_valid: boolean; orphan_count: number; cycle_count: number }>('/lineage/validate'),

  /** Search nodes by name, type, description, owner, or system */
  searchNodes: (query: string, limit: number = 20) =>
    fetchApi<SearchResult[]>(`/lineage/search?q=${encodeURIComponent(query)}&limit=${limit}`),
};

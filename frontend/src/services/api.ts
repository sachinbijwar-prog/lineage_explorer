import type { ImpactResponse, LineageDirection, LineageResponse } from '../types/graph';

const API_BASE_URL = '/api/v1';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep the HTTP status text when the response body is not JSON.
    }
    throw new Error(`API error: ${message}`);
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

export interface PathResponse {
  paths: string[][];
}

export const api = {
  testConnection: () => fetchApi<{ neo4j_status: string }>('/lineage/test'),

  seedGraph: () => fetchApi<{ status: string }>('/lineage/seed', { method: 'POST' }),

  getLineage: (nodeId: string, direction: LineageDirection = 'both', depth: number = 10) =>
    fetchApi<LineageResponse>(
      `/lineage/${encodeURIComponent(nodeId)}?direction=${encodeURIComponent(direction)}&depth=${depth}`,
    ),

  getUpstreamLineage: (nodeId: string, depth: number = 10) =>
    fetchApi<LineageResponse>(`/lineage/upstream/${encodeURIComponent(nodeId)}?depth=${depth}`),

  getDownstreamLineage: (nodeId: string, depth: number = 10) =>
    fetchApi<LineageResponse>(`/lineage/downstream/${encodeURIComponent(nodeId)}?depth=${depth}`),

  getImpactAnalysis: (nodeId: string, depth: number = 10) =>
    fetchApi<ImpactResponse>(`/lineage/impact/${encodeURIComponent(nodeId)}?depth=${depth}`),

  validateGraph: () =>
    fetchApi<{ is_valid: boolean; orphan_count: number; cycle_count: number }>('/lineage/validate'),

  searchNodes: (query: string, limit: number = 20) =>
    fetchApi<SearchResult[]>(`/lineage/search?q=${encodeURIComponent(query)}&limit=${limit}`),

  getAllNodes: () =>
    fetchApi<SearchResult[]>('/lineage/nodes'),

  getPath: (sourceId: string, targetId: string, depth: number = 10) =>
    fetchApi<PathResponse>(
      `/path/${encodeURIComponent(sourceId)}/${encodeURIComponent(targetId)}?depth=${depth}`,
    ),

  triggerScan: (path: string, loadToNeo4j: boolean = true) =>
    fetchApi<{
      status: string;
      tables: number;
      sql_files: number;
      shell_scripts: number;
      cron_jobs: number;
      relationships: number;
      loaded_to_neo4j: boolean;
      errors: string[];
    }>('/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, load_to_neo4j: loadToNeo4j }),
    }),

  ingestSql: (directoryPath?: string) =>
    fetchApi<{ nodes_created: number; relationships_created: number }>('/ingestion/sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory_path: directoryPath }),
    }),

  ingestInformatica: (directoryPath?: string) =>
    fetchApi<{ nodes_created: number; relationships_created: number }>('/ingestion/informatica', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory_path: directoryPath }),
    }),

  fetchLineage: (nodeId: string, direction: LineageDirection = 'both', depth: number = 10) =>
    api.getLineage(nodeId, direction, depth),

  fetchPath: (sourceId: string, targetId: string, depth: number = 10) =>
    api.getPath(sourceId, targetId, depth),
};

export default api;

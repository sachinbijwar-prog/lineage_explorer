export interface NodeData {
  id: string;
  type: string;
  description?: string;
  owner?: string;
  system?: string;
  role?: 'origin' | 'impacted';
}

export interface EdgeData {
  source: string;
  target: string;
  relationship: string;
}

export interface Node {
  data: NodeData;
}

export interface Edge {
  data: EdgeData;
}

export interface LineageResponse {
  nodes: Node[];
  edges: Edge[];
}

export interface ImpactSummary {
  affected_node_count: number;
  impact_depth: number;
}

export interface ImpactResponse {
  origin_node: string;
  nodes: Node[];
  edges: Edge[];
  impact_summary: ImpactSummary;
}

export type LineageDirection = 'upstream' | 'downstream' | 'both';
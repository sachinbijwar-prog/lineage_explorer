import { useCallback, useEffect, useState } from 'react';
import { GraphCanvas } from './components/GraphCanvas';
import { SearchBar } from './components/SearchBar';
import PathHighlighter from './components/PathHighlighter';
import api from './services/api';
import type { Node, Edge, ImpactSummary } from './types/graph';
import './App.css';

function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [impactSummary, setImpactSummary] = useState<ImpactSummary | null>(null);
  const [viewMode, setViewMode] = useState<'lineage' | 'impact'>('lineage');

  // Default start node for demo
  const DEFAULT_NODE = 'sales_orders';

  const loadLineage = useCallback(async (nodeId: string = DEFAULT_NODE, direction: 'upstream' | 'downstream' | 'both' = 'both', depth: number = 10) => {
    setLoading(true);
    setError(null);
    setSelectedNode(nodeId);
    setImpactSummary(null);
    setViewMode('lineage');

    try {
      const data = await api.getLineage(nodeId, direction, depth);
      setNodes(data.nodes);
      setEdges(data.edges);
      setStatus(`Loaded ${data.nodes.length} nodes and ${data.edges.length} edges`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lineage');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadImpactAnalysis = useCallback(async (nodeId: string, depth: number = 10) => {
    setLoading(true);
    setError(null);
    setSelectedNode(nodeId);

    try {
      const data = await api.getImpactAnalysis(nodeId, depth);
      setNodes(data.nodes);
      setEdges(data.edges);
      setImpactSummary(data.impact_summary);
      setViewMode('impact');
      setStatus(`Impact Analysis: ${data.impact_summary.affected_node_count} nodes impacted across ${data.impact_summary.impact_depth} levels`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load impact analysis');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSeedGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.seedGraph();
      setStatus(`Graph seeded: ${result.status}`);
      // Reload lineage after seeding
      await loadLineage(DEFAULT_NODE);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to seed graph');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (nodeId: string) => {
    // Only reload if clicking a different node or if no node is selected
    if (nodeId !== selectedNode) {
      loadLineage(nodeId);
    }
    // If same node is clicked, just ensure it's selected (no reload needed)
  };

  useEffect(() => {
    // Load initial graph on mount
    loadLineage();
  }, [loadLineage]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Enterprise Lineage Explorer</h1>
<div className="header-controls">
          <SearchBar onNodeSelect={handleNodeClick} />
          <PathHighlighter />
          <button onClick={handleSeedGraph} disabled={loading}>
            Seed Demo Graph
          </button>
          <button onClick={() => loadLineage(DEFAULT_NODE)} disabled={loading}>
            Reset View
          </button>
        </div>
      </header>

      <div className="app-content">
        <div className="graph-container">
          {loading && nodes.length === 0 && (
            <div className="loading">Loading graph...</div>
          )}
          {error && <div className="error">Error: {error}</div>}
          {status && <div className="status">Status: {status}</div>}
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            onNodeClick={handleNodeClick}
          />
        </div>

        {selectedNode && (
          <aside className="details-panel">
            <h2>Node Details</h2>
            
            {viewMode === 'impact' && impactSummary && (
              <div className="impact-summary">
                <h3>Impact Summary</h3>
                <p><strong>Origin Node:</strong> {selectedNode}</p>
                <p><strong>Nodes Impacted:</strong> {impactSummary.affected_node_count}</p>
                <p><strong>Impact Depth:</strong> {impactSummary.impact_depth} level(s)</p>
              </div>
            )}
            
            <div className="node-info">
              <p><strong>ID:</strong> {selectedNode}</p>
              {nodes.find((n) => n.data.id === selectedNode) && (
                <>
                  <p><strong>Type:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.type}</p>
                  <p><strong>Description:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.description}</p>
                  <p><strong>Owner:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.owner}</p>
                  <p><strong>System:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.system}</p>
                  {nodes.find((n) => n.data.id === selectedNode)?.data.role && (
                    <p><strong>Role:</strong> <span className={`role-badge role-${nodes.find((n) => n.data.id === selectedNode)?.data.role}`}>{nodes.find((n) => n.data.id === selectedNode)?.data.role}</span></p>
                  )}
                </>
              )}
            </div>
            <div className="panel-actions">
              <button onClick={() => loadLineage(selectedNode, 'upstream', 10)}>
                Show Upstream
              </button>
              <button onClick={() => loadLineage(selectedNode, 'downstream', 10)}>
                Show Downstream
              </button>
              <button className="impact-button" onClick={() => loadImpactAnalysis(selectedNode, 10)}>
                Show Impact Analysis
              </button>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

export default App;
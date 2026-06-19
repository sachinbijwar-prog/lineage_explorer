import { useCallback, useEffect, useState } from 'react';
import { GraphCanvas } from './components/GraphCanvas';
import { SearchBar } from './components/SearchBar';
import PathHighlighter from './components/PathHighlighter';
import api from './services/api';
import type { Node, Edge, ImpactSummary } from './types/graph';
import type { SearchResult } from './services/api';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState<'landing' | 'explorer'>('landing');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [impactSummary, setImpactSummary] = useState<ImpactSummary | null>(null);
  const [viewMode, setViewMode] = useState<'lineage' | 'impact'>('lineage');
  const [highlightedPaths, setHighlightedPaths] = useState<string[][]>([]);

  // Navigation sidebar states
  const [leftPanelTab, setLeftPanelTab] = useState<'catalog' | 'diagnostics'>('catalog');
  const [catalogNodes, setCatalogNodes] = useState<SearchResult[]>([]);
  const [catalogSearchQuery, setCatalogSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<{ [key: string]: boolean }>({
    TABLE: true,
    SQL_SCRIPT: true,
    SHELL_SCRIPT: false,
    CRON_JOB: false,
    WORKFLOW: true,
    MAPPING: true,
    OTHER: false,
  });

  // Diagnostics states
  const [validationStats, setValidationStats] = useState<{ is_valid: boolean; orphan_count: number; cycle_count: number } | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('UNKNOWN');

  // Default start node for demo
  const DEFAULT_NODE = 'sales_orders';

  const loadDiagnostics = useCallback(async () => {
    try {
      const conn = await api.testConnection();
      setConnectionStatus(conn.neo4j_status);
      const stats = await api.validateGraph();
      setValidationStats(stats);
      const allNodes = await api.getAllNodes();
      setCatalogNodes(allNodes);
    } catch (err) {
      console.error('Failed to load diagnostics:', err);
    }
  }, []);

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
      await loadDiagnostics();
      await loadLineage(DEFAULT_NODE);
      setCurrentPage('explorer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to seed graph');
    } finally {
      setLoading(false);
    }
  };

  const handleScanWorkspace = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.triggerScan('c:/git/lineage_explorer', true);
      setStatus(`Scan completed: ${result.status} (Tables: ${result.tables}, SQL: ${result.sql_files}, Shell: ${result.shell_scripts}, Cron: ${result.cron_jobs}, Edges: ${result.relationships})`);
      await loadDiagnostics();
      await loadLineage('TABLE:FAO_TRADE_FACT');
      setCurrentPage('explorer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scan workspace');
    } finally {
      setLoading(false);
    }
  };

  const handleIngestSql = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.ingestSql();
      setStatus(`SQL Ingestion completed: created ${result.nodes_created} nodes and ${result.relationships_created} relationships`);
      await loadDiagnostics();
      await loadLineage('FACT_SALES');
      setCurrentPage('explorer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to ingest SQL');
    } finally {
      setLoading(false);
    }
  };

  const handleIngestInformatica = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.ingestInformatica();
      setStatus(`Informatica Ingestion completed: created ${result.nodes_created} nodes and ${result.relationships_created} relationships`);
      await loadDiagnostics();
      await loadLineage('WF_SALES_DAILY_LOAD');
      setCurrentPage('explorer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to ingest Informatica XML');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (nodeId: string) => {
    if (nodeId !== selectedNode) {
      loadLineage(nodeId);
    }
  };

  useEffect(() => {
    loadDiagnostics();
    loadLineage();
  }, [loadDiagnostics, loadLineage]);

  // Group catalog nodes by generalized categories
  const getCategorizedNodes = () => {
    const categories: { [key: string]: SearchResult[] } = {
      TABLE: [],
      SQL_SCRIPT: [],
      SHELL_SCRIPT: [],
      CRON_JOB: [],
      WORKFLOW: [],
      MAPPING: [],
      OTHER: [],
    };

    const queryLower = catalogSearchQuery.trim().toLowerCase();
    const filtered = catalogNodes.filter(node => 
      node.id.toLowerCase().includes(queryLower) ||
      (node.type && node.type.toLowerCase().includes(queryLower)) ||
      (node.system && node.system.toLowerCase().includes(queryLower))
    );

    filtered.forEach(node => {
      const type = (node.type || '').toUpperCase();
      if (type.includes('TABLE') || type.includes('FILE')) {
        categories.TABLE.push(node);
      } else if (type.includes('SQL_SCRIPT') || type.includes('SQL')) {
        categories.SQL_SCRIPT.push(node);
      } else if (type.includes('SHELL') || type.includes('SH') || type.includes('SHELL_SCRIPT')) {
        categories.SHELL_SCRIPT.push(node);
      } else if (type.includes('CRON') || type.includes('CRON_JOB')) {
        categories.CRON_JOB.push(node);
      } else if (type.includes('WORKFLOW')) {
        categories.WORKFLOW.push(node);
      } else if (type.includes('MAPPING')) {
        categories.MAPPING.push(node);
      } else {
        categories.OTHER.push(node);
      }
    });

    return categories;
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  // Render Landing Page
  if (currentPage === 'landing') {
    return (
      <div className="app dark-theme landing-page">
        <header className="app-header glassmorphic">
          <div className="logo-container">
            <span className="logo-icon">🌐</span>
            <h1>Enterprise Lineage Explorer</h1>
          </div>
          <div className="header-status-badge">
            <span className={`status-dot ${connectionStatus === 'CONNECTED' ? 'online' : 'offline'}`} />
            Neo4j: {connectionStatus}
          </div>
        </header>

        <main className="landing-main">
          <section className="hero-section">
            <h2 className="hero-title">End-to-End Data Lineage & Dependency Tracing</h2>
            <p className="hero-subtitle">
              Map operations, files, tables, and jobs to visualize data pipelines, execute validation diagnostics, and run impact analysis instantly.
            </p>
            <div className="hero-actions">
              <button className="primary-btn pulse-glow" onClick={() => setCurrentPage('explorer')}>
                Launch Explorer Workspace →
              </button>
            </div>
          </section>

          <section className="quick-stats-grid">
            <div className="stats-card glassmorphic hover-scale">
              <h3>Database Connection</h3>
              <div className="stat-value text-indigo">{connectionStatus}</div>
              <p className="stat-desc">
                Active connection to Neo4j database graph store.
              </p>
              <div className="card-action">
                <button onClick={loadDiagnostics} className="secondary-btn btn-sm">Refresh Health</button>
              </div>
            </div>

            <div className="stats-card glassmorphic hover-scale">
              <h3>System Ingestion</h3>
              <div className="stat-value text-emerald">{catalogNodes.length}</div>
              <p className="stat-desc">
                Total catalog nodes successfully scanned and parsed in the lineage graph.
              </p>
              <div className="card-action" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button onClick={handleSeedGraph} className="secondary-btn btn-sm" disabled={loading}>Seed Demo</button>
                <button onClick={handleScanWorkspace} className="secondary-btn btn-sm" disabled={loading}>Scan Directory</button>
                <button onClick={handleIngestSql} className="secondary-btn btn-sm" disabled={loading}>Ingest SQL</button>
                <button onClick={handleIngestInformatica} className="secondary-btn btn-sm" style={{ background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', color: '#fff' }} disabled={loading}>Ingest Informatica</button>
              </div>
            </div>

            <div className="stats-card glassmorphic hover-scale">
              <h3>Graph Integrity</h3>
              {validationStats ? (
                <>
                  <div className="validation-summary">
                    <div className="val-item">
                      <span className="val-label">Cycles:</span>
                      <span className={`val-count ${validationStats.cycle_count > 0 ? 'alert' : 'clean'}`}>
                        {validationStats.cycle_count}
                      </span>
                    </div>
                    <div className="val-item">
                      <span className="val-label">Orphans:</span>
                      <span className="val-count neutral">
                        {validationStats.orphan_count}
                      </span>
                    </div>
                  </div>
                  <p className="stat-desc">
                    {validationStats.is_valid ? '✅ No cyclic dependencies detected in database.' : '⚠️ Cycles detected in database dependencies.'}
                  </p>
                </>
              ) : (
                <div className="loading-small">Running checks...</div>
              )}
              <div className="card-action">
                <button onClick={loadDiagnostics} className="secondary-btn btn-sm">Run Check</button>
              </div>
            </div>
          </section>
        </main>
      </div>
    );
  }

  // Render main explorer page
  const categorized = getCategorizedNodes();

  return (
    <div className="app dark-theme explorer-page">
      <header className="app-header glassmorphic">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button className="back-btn" onClick={() => setCurrentPage('landing')} title="Back to overview">
            ← Overview
          </button>
          <div className="logo-container">
            <h1>Workspace Explorer</h1>
          </div>
        </div>
        <div className="header-controls">
          <SearchBar onNodeSelect={handleNodeClick} />
          <PathHighlighter onPathsHighlight={setHighlightedPaths} />
          <button onClick={() => loadLineage(DEFAULT_NODE)} disabled={loading}>
            Reset View
          </button>
        </div>
      </header>

      <div className="app-content">
        {/* Left Sidebar Panel */}
        <aside className="sidebar-panel left-panel glassmorphic">
          <div className="sidebar-tabs">
            <button 
              className={`sidebar-tab-btn ${leftPanelTab === 'catalog' ? 'active' : ''}`}
              onClick={() => setLeftPanelTab('catalog')}
            >
              📂 Data Catalog
            </button>
            <button 
              className={`sidebar-tab-btn ${leftPanelTab === 'diagnostics' ? 'active' : ''}`}
              onClick={() => setLeftPanelTab('diagnostics')}
            >
              🩺 Diagnostics
            </button>
          </div>

          <div className="sidebar-content-area">
            {leftPanelTab === 'catalog' ? (
              <div className="catalog-browser">
                <div className="search-filter-wrapper">
                  <input
                    type="text"
                    placeholder="Filter catalog nodes..."
                    value={catalogSearchQuery}
                    onChange={(e) => setCatalogSearchQuery(e.target.value)}
                    className="catalog-search-input"
                  />
                  {catalogSearchQuery && (
                    <button className="clear-filter-btn" onClick={() => setCatalogSearchQuery('')}>
                      ×
                    </button>
                  )}
                </div>

                <div className="catalog-accordion">
                  {Object.entries(categorized).map(([category, items]) => {
                    const isExpanded = expandedCategories[category];
                    return (
                      <div key={category} className="accordion-group">
                        <button 
                          className="accordion-header" 
                          onClick={() => toggleCategory(category)}
                        >
                          <span className="accordion-chevron">{isExpanded ? '▼' : '▶'}</span>
                          <span className="accordion-title">{category.replace('_', ' ')}s</span>
                          <span className="category-badge">{items.length}</span>
                        </button>
                        
                        {isExpanded && (
                          <ul className="accordion-item-list">
                            {items.length > 0 ? (
                              items.map(item => (
                                <li 
                                  key={item.id} 
                                  className={`accordion-item ${selectedNode === item.id ? 'active' : ''}`}
                                  onClick={() => handleNodeClick(item.id)}
                                >
                                  <div className="item-name" title={item.id}>{item.id}</div>
                                  {item.system && <span className="item-system-badge">{item.system}</span>}
                                </li>
                              ))
                            ) : (
                              <li className="accordion-item-empty">No nodes in this category</li>
                            )}
                          </ul>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="diagnostics-panel-content">
                <div className="diagnostics-group">
                  <h4>Neo4j Health</h4>
                  <div className="diagnostic-row">
                    <span>Database Status:</span>
                    <span className={`status-text ${connectionStatus === 'CONNECTED' ? 'online' : 'offline'}`}>
                      {connectionStatus}
                    </span>
                  </div>
                </div>

                <div className="diagnostics-group">
                  <h4>Graph Validation</h4>
                  {validationStats ? (
                    <>
                      <div className="diagnostic-row">
                        <span>Graph Health:</span>
                        <span className={`status-text ${validationStats.is_valid ? 'online' : 'offline'}`}>
                          {validationStats.is_valid ? 'Healthy' : 'Anomaly Detected'}
                        </span>
                      </div>
                      <div className="diagnostic-row">
                        <span>Cyclic Dependencies:</span>
                        <span className={`diagnostic-val ${validationStats.cycle_count > 0 ? 'danger' : 'success'}`}>
                          {validationStats.cycle_count}
                        </span>
                      </div>
                      <div className="diagnostic-row">
                        <span>Orphaned Assets:</span>
                        <span className="diagnostic-val neutral">
                          {validationStats.orphan_count}
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="loading-small">Checking...</div>
                  )}
                  <button onClick={loadDiagnostics} className="validation-run-btn" disabled={loading}>
                    Run Integrity Diagnostics
                  </button>
                </div>

                <div className="diagnostics-group ingestion-controls">
                  <h4>Workspace Ingestion</h4>
                  <p className="ingestion-desc">Target path: <code>c:/git/lineage_explorer</code></p>
                  <button onClick={handleScanWorkspace} className="ingestion-btn scan-btn" disabled={loading}>
                    Scan Workspace Scripts
                  </button>
                  <button onClick={handleIngestSql} className="ingestion-btn scan-btn" style={{ marginTop: '0.5rem', background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' }} disabled={loading}>
                    Ingest SQL Lineage
                  </button>
                  <button onClick={handleIngestInformatica} className="ingestion-btn scan-btn" style={{ marginTop: '0.5rem', background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }} disabled={loading}>
                    Ingest Informatica XML
                  </button>
                  <button onClick={handleSeedGraph} className="ingestion-btn seed-btn" style={{ marginTop: '0.5rem' }} disabled={loading}>
                    Reload Demo Seed Graph
                  </button>
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Central Workspace Area */}
        <div className="graph-container">
          {loading && nodes.length === 0 && (
            <div className="loading glassmorphic">Loading lineage workspace...</div>
          )}
          {error && <div className="error glassmorphic">Error: {error}</div>}
          {status && <div className="status glassmorphic">{status}</div>}
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            onNodeClick={handleNodeClick}
            highlightedPaths={highlightedPaths}
          />
        </div>

        {/* Right Details Panel */}
        {selectedNode && (
          <aside className="details-panel glassmorphic">
            <h2>Node Metadata</h2>
            
            {viewMode === 'impact' && impactSummary && (
              <div className="impact-summary">
                <h3>Impact Summary</h3>
                <p><strong>Origin Node:</strong> {selectedNode}</p>
                <p><strong>Nodes Impacted:</strong> {impactSummary.affected_node_count}</p>
                <p><strong>Impact Depth:</strong> {impactSummary.impact_depth} level(s)</p>
                
                <div style={{ marginTop: '0.75rem' }}>
                  <strong style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.8rem', color: 'var(--accent-amber)' }}>
                    Impacted Downstream Nodes:
                  </strong>
                  <div className="impacted-nodes-list" style={{ 
                    maxHeight: '130px', 
                    overflowY: 'auto', 
                    background: 'rgba(0,0,0,0.25)', 
                    borderRadius: '6px',
                    padding: '0.35rem 0.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                    border: '1px solid rgba(245, 158, 11, 0.2)'
                  }}>
                    {nodes
                      .filter(n => n.data.role === 'impacted')
                      .map(n => (
                        <div 
                          key={n.data.id} 
                          className="impacted-list-item"
                          onClick={() => handleNodeClick(n.data.id)}
                          style={{ 
                            fontSize: '0.75rem', 
                            color: 'var(--text-gray-300)', 
                            cursor: 'pointer',
                            padding: '0.25rem 0.35rem',
                            borderRadius: '4px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '170px' }} title={n.data.id}>
                            {n.data.id}
                          </span>
                          <span style={{ 
                            fontSize: '0.65rem', 
                            opacity: 0.85, 
                            background: 'rgba(255,255,255,0.08)', 
                            color: 'var(--text-gray-300)',
                            padding: '1px 4px', 
                            borderRadius: '3px', 
                            fontWeight: 600, 
                            textTransform: 'uppercase' 
                          }}>
                            {n.data.type || 'unknown'}
                          </span>
                        </div>
                      ))}
                    {nodes.filter(n => n.data.role === 'impacted').length === 0 && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-gray-500)', fontStyle: 'italic', padding: '0.25rem' }}>
                        No downstream nodes impacted.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            <div className="node-info">
              <p><strong>ID:</strong> {selectedNode}</p>
              {nodes.find((n) => n.data.id === selectedNode) && (
                <>
                  <p><strong>Type:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.type}</p>
                  <p><strong>Description:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.description || 'No description provided'}</p>
                  <p><strong>Owner:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.owner || 'N/A'}</p>
                  <p><strong>System:</strong> {nodes.find((n) => n.data.id === selectedNode)?.data.system || 'N/A'}</p>
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
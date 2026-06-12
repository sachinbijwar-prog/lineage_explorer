import { useCallback, useEffect, useRef, useState } from 'react';
import cytoscape, { ElementDefinition, LayoutOptions } from 'cytoscape';
import dagre from 'cytoscape-dagre';
import type { Node, Edge } from '../types/graph';
import './GraphCanvas.css';

// Register dagre layout with Cytoscape
cytoscape.use(dagre);

interface GraphCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodeClick?: (nodeId: string) => void;
  highlightedPaths?: string[][];
}

// Node color mapping based on type
const getNodeColor = (type: string): string => {
  const assetTypes = ['hive_table', 'flat_file', 'handshake_file', 'trigger_file'];
  const processTypes = ['spark_job', 'beeline', 'shell_script'];

  if (assetTypes.includes(type)) return '#3b82f6'; // blue
  if (processTypes.includes(type)) return '#10b981'; // green
  return '#6b7280'; // gray
};

// Node shape mapping based on type
const getNodeShape = (type: string): 'rectangle' | 'diamond' | 'ellipse' => {
  const assetTypes = ['hive_table', 'flat_file', 'handshake_file', 'trigger_file'];
  const processTypes = ['spark_job', 'beeline', 'shell_script'];

  if (assetTypes.includes(type)) return 'rectangle';
  if (processTypes.includes(type)) return 'diamond';
  return 'ellipse';
};

export function GraphCanvas({ nodes, edges, onNodeClick, highlightedPaths }: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  const initializeGraph = useCallback(() => {
    if (!containerRef.current) return;

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    // Convert nodes and edges to Cytoscape format
    const elements: ElementDefinition[] = [
      ...nodes.map((node) => ({
        data: {
          id: node.data.id,
          label: node.data.id,
          type: node.data.type,
          description: node.data.description,
          owner: node.data.owner,
          system: node.data.system,
          role: node.data.role,
        },
      })),
      ...edges.map((edge) => ({
        data: {
          source: edge.data.source,
          target: edge.data.target,
          label: edge.data.relationship,
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: cytoscape.NodeSingular) => getNodeColor(ele.data('type') as string),
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '70px',
            'font-size': '11px',
            'text-outline-color': '#ffffff',
            'text-outline-width': 1,
            shape: (ele: cytoscape.NodeSingular) => getNodeShape(ele.data('type') as string),
            width: '90px',
            height: '70px',
            'padding': '5px',
          },
        },
        {
          selector: 'node[role="origin"]',
          style: {
            'border-width': 4,
            'border-color': '#f59e0b',
          },
        },
        {
          selector: 'node[role="impacted"]',
          style: {
            'border-width': 3,
            'border-color': '#ef4444',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#9ca3af',
            'target-arrow-color': '#9ca3af',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#6366f1',
          },
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-width': 4,
            'border-color': '#f59e0b',
            'background-opacity': 0.8,
          },
        },
        {
          selector: 'edge.highlighted',
          style: {
            width: 4,
            'line-color': '#f59e0b',
            'target-arrow-color': '#f59e0b',
          },
        },
        {
          selector: 'node.dimmed',
          style: {
            opacity: 0.3,
          },
        },
        {
          selector: 'edge.dimmed',
          style: {
            opacity: 0.3,
          },
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSpacing: 100,
        rankSep: 150,
        animate: true,
        animationDuration: 500,
      } as LayoutOptions,
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    // Handle node click
    cy.on('tap', 'node', (evt: cytoscape.EventObject) => {
      const node = evt.target;
      if (onNodeClick) {
        onNodeClick(node.id());
      }
    });

    // Update zoom level display
    cy.on('zoom', () => {
      setZoomLevel(Math.round(cy.zoom() * 100));
    });

    cyRef.current = cy;

    // Fit graph to view
    setTimeout(() => {
      cy.fit(50 as any);
    }, 100);
  }, [nodes, edges, onNodeClick]);

  // Navigation controls
  const handleZoomIn = useCallback(() => {
    if (cyRef.current) {
      const currentZoom = cyRef.current.zoom();
      cyRef.current.animate({
        zoom: Math.min(currentZoom * 1.3, 3),
        duration: 200,
      });
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (cyRef.current) {
      const currentZoom = cyRef.current.zoom();
      cyRef.current.animate({
        zoom: Math.max(currentZoom / 1.3, 0.2),
        duration: 200,
      });
    }
  }, []);

  const handleFitToScreen = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.animate({
        fit: { eles: cyRef.current.elements(), padding: 50 },
        duration: 300,
      });
    }
  }, []);

  const handleResetView = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.animate({
        zoom: 1,
        pan: { x: 0, y: 0 },
        duration: 300,
      });
    }
  }, []);

  useEffect(() => {
    initializeGraph();

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [initializeGraph]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    if (highlightedPaths && highlightedPaths.length > 0) {
      const pathNodes = new Set<string>();
      highlightedPaths.forEach(path => {
        path.forEach(nodeId => pathNodes.add(nodeId));
      });

      const pathEdges = new Set<string>();
      highlightedPaths.forEach(path => {
        for (let i = 0; i < path.length - 1; i++) {
          const u = path[i];
          const v = path[i + 1];
          cy.edges().forEach(edge => {
            const src = edge.data('source');
            const tgt = edge.data('target');
            if ((src === u && tgt === v) || (src === v && tgt === u)) {
              pathEdges.add(edge.id());
            }
          });
        }
      });

      cy.elements().forEach((ele: any) => {
        if (ele.isNode()) {
          if (pathNodes.has(ele.id())) {
            ele.addClass('highlighted');
            ele.removeClass('dimmed');
          } else {
            ele.removeClass('highlighted');
            ele.addClass('dimmed');
          }
        } else if (ele.isEdge()) {
          if (pathEdges.has(ele.id())) {
            ele.addClass('highlighted');
            ele.removeClass('dimmed');
          } else {
            ele.removeClass('highlighted');
            ele.addClass('dimmed');
          }
        }
      });
    } else {
      cy.elements().removeClass('highlighted').removeClass('dimmed');
    }
  }, [highlightedPaths, nodes, edges]);

  return (
    <div className="graph-canvas-container">
      <div className="graph-canvas" ref={containerRef} />
      
      {/* Navigation Toolbar */}
      <div className="navigation-toolbar">
        <button 
          className="nav-button" 
          onClick={handleZoomIn} 
          title="Zoom In"
          aria-label="Zoom In"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
            <path d="M11 8v6M8 11h6" />
          </svg>
        </button>
        
        <button 
          className="nav-button" 
          onClick={handleZoomOut} 
          title="Zoom Out"
          aria-label="Zoom Out"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
            <path d="M8 11h6" />
          </svg>
        </button>
        
        <div className="nav-separator" />
        
        <button 
          className="nav-button" 
          onClick={handleFitToScreen} 
          title="Fit to Screen"
          aria-label="Fit to Screen"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
          </svg>
        </button>
        
        <button 
          className="nav-button" 
          onClick={handleResetView} 
          title="Reset View"
          aria-label="Reset View"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
            <path d="M3 3v5h5" />
          </svg>
        </button>
        
        <div className="nav-separator" />
        
        <div className="zoom-indicator">
          {zoomLevel}%
        </div>
      </div>
    </div>
  );
}

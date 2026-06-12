import { useState } from 'react';
import api from '../services/api';

interface PathHighlighterProps {
  onPathsHighlight?: (paths: string[][]) => void;
}

export default function PathHighlighter({ onPathsHighlight }: PathHighlighterProps) {
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [paths, setPaths] = useState<string[][]>([]);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    setError('');
    if (!source.trim() || !target.trim()) {
      setError('Please provide both Source and Target.');
      return;
    }
    try {
      const data = await api.getPath(source.trim(), target.trim());
      setPaths(data.paths);
      if (onPathsHighlight) {
        onPathsHighlight(data.paths);
      }
    } catch (e: any) {
      // API error messages are embedded in Error.message when fetchApi throws them
      const errMsg = e.message || 'Failed to fetch path';
      setError(errMsg.replace('API error: ', ''));
      setPaths([]);
      if (onPathsHighlight) {
        onPathsHighlight([]);
      }
    }
  };

  const handleClear = () => {
    setSource('');
    setTarget('');
    setPaths([]);
    setError('');
    if (onPathsHighlight) {
      onPathsHighlight([]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <input
          placeholder="Source Node"
          value={source}
          onChange={e => setSource(e.target.value)}
          style={{
            marginRight: '0.5rem',
            padding: '0.375rem 0.75rem',
            borderRadius: '6px',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'white',
            outline: 'none',
            fontSize: '0.875rem'
          }}
        />
        <input
          placeholder="Target Node"
          value={target}
          onChange={e => setTarget(e.target.value)}
          style={{
            marginRight: '0.5rem',
            padding: '0.375rem 0.75rem',
            borderRadius: '6px',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'white',
            outline: 'none',
            fontSize: '0.875rem'
          }}
        />
        <button onClick={handleSubmit} style={{ marginRight: '0.5rem' }}>Highlight Path</button>
        {(source || target || paths.length > 0) && (
          <button onClick={handleClear} style={{ background: 'rgba(239, 68, 68, 0.2)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
            Clear
          </button>
        )}
      </div>
      {error && <span style={{ color: '#fecaca', fontSize: '0.75rem', marginTop: '2px', fontWeight: 500 }}>{error}</span>}
      {paths.length > 0 && (
        <span style={{ color: '#d1fae5', fontSize: '0.75rem', marginTop: '2px', fontWeight: 500 }}>
          Paths found: {paths.length} ({paths[0].length} nodes each)
        </span>
      )}
    </div>
  );
}
import { useState } from 'react';
import api from '../services/api';

export default function PathHighlighter() {
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [path, setPath] = useState<string[]>([]);
  const [error, setError] = useState('');

const handleSubmit = async () => {
    setError('');
    try {
      const data = await api.getPath(source, target);
      setPath(data.path);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to fetch path');
    }
  };

  return (
    <div style={{ marginTop: '1rem' }}>
      <h3>Path Highlighting</h3>
      <input
        placeholder="Source ID"
        value={source}
        onChange={e => setSource(e.target.value)}
        style={{ marginRight: '0.5rem' }}
      />
      <input
        placeholder="Target ID"
        value={target}
        onChange={e => setTarget(e.target.value)}
        style={{ marginRight: '0.5rem' }}
      />
      <button onClick={handleSubmit}>Highlight Path</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {path.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <strong>Path:</strong> {path.join(' → ')}
        </div>
      )}
    </div>
  );
}
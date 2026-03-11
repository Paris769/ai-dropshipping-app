import { useEffect, useState } from 'react';

export default function Home() {
  const [status, setStatus] = useState<string>('checking');

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const data = await res.json();
          setStatus(data.status);
        } else {
          setStatus('error');
        }
      } catch (err) {
        setStatus('error');
      }
    }
    checkHealth();
  }, []);

  return (
    <div style={{ padding: '1rem' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
        AI Dropshipping Control Panel
      </h1>
      <p>Backend status: <strong>{status}</strong></p>
    </div>
  );
}

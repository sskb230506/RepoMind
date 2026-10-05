import { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { HealthStatus } from './components/HealthStatus';
import { Features } from './components/Features';
import { ArchitectureView } from './components/ArchitectureView';
import { Footer } from './components/Footer';

interface HealthData {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export function App() {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      // First try relative /health (Vite proxy / production reverse proxy)
      const res = await fetch('/health', {
        headers: { Accept: 'application/json' },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data: HealthData = await res.json();
      const elapsed = Math.round(performance.now() - startTime);
      setHealthData(data);
      setLatency(elapsed);
    } catch (err: unknown) {
      // If relative fails (e.g. if vite proxy is not routed), attempt direct call to backend port 8000
      try {
        const directRes = await fetch('http://localhost:8000/health', {
          headers: { Accept: 'application/json' },
        });

        if (!directRes.ok) {
          throw new Error(`HTTP ${directRes.status}: ${directRes.statusText}`);
        }

        const data: HealthData = await directRes.json();
        const elapsed = Math.round(performance.now() - startTime);
        setHealthData(data);
        setLatency(elapsed);
      } catch (directErr: unknown) {
        const message = directErr instanceof Error ? directErr.message : 'Failed to connect to backend';
        setError(message);
        setHealthData(null);
        setLatency(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  const isHealthy = healthData ? healthData.status === 'healthy' : error ? false : null;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
      <Navbar isHealthy={isHealthy} onRefreshHealth={fetchHealth} />
      <main className="flex-1">
        <Hero />
        <HealthStatus
          data={healthData}
          loading={loading}
          error={error}
          latency={latency}
          onRefresh={fetchHealth}
        />
        <Features />
        <ArchitectureView />
      </main>
      <Footer />
    </div>
  );
}

export default App;

import React, { useState } from 'react';
import { Activity, RefreshCw, CheckCircle2, XCircle, Clock, Server, Code, Copy, Check } from 'lucide-react';

interface HealthData {
  status: string;
  service: string;
  version: string;
  environment: string;
}

interface HealthStatusProps {
  data: HealthData | null;
  loading: boolean;
  error: string | null;
  latency: number | null;
  onRefresh: () => void;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({
  data,
  loading,
  error,
  latency,
  onRefresh,
}) => {
  const [copied, setCopied] = useState(false);

  const copyJson = () => {
    if (data) {
      navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <section id="health" className="py-12 scroll-mt-20">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-purple-400" />
              <h2 className="text-xl font-bold text-white tracking-tight">Backend Health Verification</h2>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Live inspection of the FastAPI health endpoint (<code className="text-purple-300 font-mono text-xs">GET /health</code>).
            </p>
          </div>

          <div className="mt-4 sm:mt-0 flex items-center space-x-3">
            <button
              onClick={onRefresh}
              disabled={loading}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Pinging...' : 'Ping Health Endpoint'}</span>
            </button>
          </div>
        </div>

        {/* Health Card Grid */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Status Tile */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-slate-400 font-medium">Service Status</div>
              <div className="mt-3 flex items-center space-x-3">
                {data?.status === 'healthy' ? (
                  <>
                    <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <div className="text-lg font-bold text-white uppercase tracking-wide">ONLINE</div>
                      <div className="text-xs text-emerald-400 font-medium">FastAPI Responsive</div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-9 h-9 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                      <XCircle className="w-5 h-5 text-rose-400" />
                    </div>
                    <div>
                      <div className="text-lg font-bold text-white uppercase tracking-wide">
                        {loading ? 'CONNECTING...' : 'DISCONNECTED'}
                      </div>
                      <div className="text-xs text-rose-400 font-medium">
                        {loading ? 'Awaiting response' : 'Service offline or blocked'}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span className="flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Roundtrip Latency:</span>
              </span>
              <span className="font-mono font-semibold text-slate-200">
                {latency !== null ? `${latency} ms` : '--'}
              </span>
            </div>
          </div>

          {/* Service Metadata Tile */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-slate-400 font-medium">Service Metadata</div>
              <div className="mt-3 space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 flex items-center space-x-1.5">
                    <Server className="w-3.5 h-3.5 text-slate-500" />
                    <span>Service:</span>
                  </span>
                  <span className="font-mono text-slate-200 font-medium">
                    {data?.service || 'repomind-backend'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Version:</span>
                  <span className="font-mono text-purple-300 font-semibold">
                    {data?.version || '0.1.0'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Environment:</span>
                  <span className="font-mono text-slate-200 capitalize">
                    {data?.environment || 'development'}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span>Protocol:</span>
              <span className="font-mono text-slate-300">HTTP/1.1 REST</span>
            </div>
          </div>

          {/* JSON Payload Inspector */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-slate-400 font-medium flex items-center space-x-1.5">
                <Code className="w-3.5 h-3.5 text-slate-500" />
                <span>Endpoint Payload</span>
              </div>
              {data && (
                <button
                  onClick={copyJson}
                  className="text-slate-400 hover:text-slate-200 text-xs flex items-center space-x-1"
                  title="Copy JSON"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </div>

            <div className="mt-3 bg-slate-950/70 rounded-xl p-3 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
              {data ? (
                <pre>{JSON.stringify(data, null, 2)}</pre>
              ) : (
                <pre className="text-slate-500">
{`{
  "status": "healthy",
  "service": "repomind-backend",
  "version": "0.1.0",
  "environment": "development"
}`}
                </pre>
              )}
            </div>

            {error && (
              <div className="mt-3 text-[11px] text-rose-400 bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
                {error} (Check if backend server is running on port 8000)
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

import React from 'react';
import { GitBranch, Github, ExternalLink, Activity } from 'lucide-react';

interface NavbarProps {
  isHealthy: boolean | null;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ isHealthy, onRefreshHealth }) => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <GitBranch className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                RepoMind
              </span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                v0.1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Codebase Intelligence</p>
          </div>
        </div>

        {/* Center Nav */}
        <nav className="hidden md:flex items-center space-x-6 text-sm text-slate-300">
          <a href="#health" className="hover:text-white transition-colors flex items-center space-x-1.5">
            <Activity className="w-4 h-4 text-purple-400" />
            <span>Health Check</span>
          </a>
          <a href="#capabilities" className="hover:text-white transition-colors">
            Capabilities
          </a>
          <a href="#architecture" className="hover:text-white transition-colors">
            Architecture
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white transition-colors flex items-center space-x-1"
          >
            <span>FastAPI Docs</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          </a>
        </nav>

        {/* Right CTA */}
        <div className="flex items-center space-x-3">
          {/* Health indicator badge */}
          <button
            onClick={onRefreshHealth}
            title="Click to re-check backend health"
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900/60 border border-slate-700 hover:border-slate-600 transition"
          >
            <span className="relative flex h-2 w-2">
              {isHealthy === true && (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </>
              )}
              {isHealthy === false && (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              )}
              {isHealthy === null && (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500 animate-pulse"></span>
              )}
            </span>
            <span className="text-slate-300">
              {isHealthy === true ? 'Backend: Healthy' : isHealthy === false ? 'Backend: Offline' : 'Checking...'}
            </span>
          </button>

          <a
            href="https://github.com/sskb230506/RepoMind"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-white transition border border-slate-700/60"
          >
            <Github className="w-4 h-4" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </div>
      </div>
    </header>
  );
};

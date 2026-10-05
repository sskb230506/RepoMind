import React from 'react';
import { Layers, FolderTree, Cpu, Box, HardDrive, Shield } from 'lucide-react';

export const ArchitectureView: React.FC = () => {
  return (
    <section id="architecture" className="py-16 scroll-mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-3">
            <Layers className="w-3.5 h-3.5" />
            <span>Monorepo Architecture</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            System Topology & Module Boundaries
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            Engineered as a clean monorepo with segregated concerns, centralized config, and containerized parity.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          {/* Tree Structure */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 font-mono text-xs">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
              <span className="text-slate-300 font-semibold flex items-center space-x-2">
                <FolderTree className="w-4 h-4 text-purple-400" />
                <span>repomind/ Workspace</span>
              </span>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest">Layout</span>
            </div>

            <div className="space-y-2 text-slate-300">
              <div className="text-purple-400 font-semibold">repomind/</div>
              <div className="pl-4 space-y-1.5">
                <div>├── <span className="text-indigo-300 font-semibold">backend/</span> <span className="text-slate-500"># FastAPI, SQLAlchemy, PostgreSQL, /health</span></div>
                <div>├── <span className="text-cyan-300 font-semibold">frontend/</span> <span className="text-slate-500"># React, TypeScript, Vite, Tailwind CSS</span></div>
                <div>├── <span className="text-amber-300 font-semibold">worker/</span> <span className="text-slate-500"># Python background task processor & queue</span></div>
                <div>├── <span className="text-emerald-300 font-semibold">tests/</span> <span className="text-slate-500"># End-to-end and cross-service test suites</span></div>
                <div>├── <span className="text-slate-400">docs/</span> <span className="text-slate-500"># Architecture, API specifications, and setup</span></div>
                <div>├── <span className="text-slate-400">scripts/</span> <span className="text-slate-500"># Developer setup, dev runners, and linting</span></div>
                <div>├── <span className="text-slate-400">docker/</span> <span className="text-slate-500"># Container definitions for all microservices</span></div>
                <div>├── <span className="text-slate-200">docker-compose.yml</span> <span className="text-slate-500"># Local orchestration</span></div>
                <div>├── <span className="text-slate-200">.env.example</span> <span className="text-slate-500"># Central environment variable manifest</span></div>
                <div>├── <span className="text-slate-200">.gitignore</span> <span className="text-slate-500"># Ignore rules</span></div>
                <div>└── <span className="text-slate-200">README.md</span> <span className="text-slate-500"># Project documentation</span></div>
              </div>
            </div>
          </div>

          {/* Component Specifications */}
          <div className="space-y-4">
            {/* Backend Spec */}
            <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-start space-x-4">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-semibold text-white">Backend Microservice</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">FastAPI</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Provides high-throughput async REST endpoints. Structured with modular v1 API routers, Pydantic settings validation, and SQLAlchemy database session pooling.
                </p>
              </div>
            </div>

            {/* Frontend Spec */}
            <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-start space-x-4">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 shrink-0">
                <Box className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-semibold text-white">Frontend Application</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">React + Vite</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Built with React 18 and Vite for instantaneous hot-reloading. Uses Tailwind CSS and a curated dark obsidian design system for maximum clarity and responsiveness.
                </p>
              </div>
            </div>

            {/* Worker Spec */}
            <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-start space-x-4">
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
                <HardDrive className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-semibold text-white">Async Background Worker</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300">Python Worker</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Decoupled worker equipped with graceful shutdown hooks and polling loops. Handles computationally intensive repository cloning, AST extraction, and dependency graph indexing.
                </p>
              </div>
            </div>

            {/* Storage Spec */}
            <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-start space-x-4">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-semibold text-white">Relational Engine</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">PostgreSQL 16</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Orchestrated with Docker Compose featuring automated healthchecks, volume persistence, and connection reuse.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

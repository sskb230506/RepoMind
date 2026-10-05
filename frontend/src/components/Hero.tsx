import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Terminal } from 'lucide-react';

export const Hero: React.FC = () => {
  return (
    <section className="relative pt-16 pb-20 overflow-hidden">
      {/* Background radial gradient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-purple-600/15 rounded-full blur-3xl pointer-events-none -z-10" />
      <div className="absolute top-1/3 left-1/3 w-[400px] h-[250px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none -z-10" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/25 text-purple-300 text-xs font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Foundation Monorepo Architecture Active</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight sm:leading-none mb-6">
          AI Codebase Intelligence <br />
          <span className="bg-gradient-to-r from-purple-400 via-indigo-300 to-blue-400 bg-clip-text text-transparent">
            Engineered for Precision
          </span>
        </h1>

        {/* Subtitle */}
        <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-300 font-normal leading-relaxed mb-10">
          Connect your GitHub repository to trace dependencies, analyze change-impact blast radiuses,
          explore Git historical evolution, and discover relevant tests across massive monorepos.
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4">
          <a
            href="#health"
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium shadow-lg shadow-purple-600/25 transition transform hover:-translate-y-0.5"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Verify System Health</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </a>

          <a
            href="#architecture"
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 font-medium border border-slate-700/80 transition transform hover:-translate-y-0.5"
          >
            <Terminal className="w-4 h-4 text-slate-400" />
            <span>Monorepo Topology</span>
          </a>
        </div>

        {/* Metric pills */}
        <div className="mt-14 pt-8 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          <div className="glass-card rounded-xl p-3.5 text-center">
            <div className="text-xs text-slate-400 font-medium">Backend Framework</div>
            <div className="text-sm font-semibold text-white mt-1">FastAPI + SQLAlchemy</div>
          </div>
          <div className="glass-card rounded-xl p-3.5 text-center">
            <div className="text-xs text-slate-400 font-medium">Relational Storage</div>
            <div className="text-sm font-semibold text-white mt-1">PostgreSQL 16</div>
          </div>
          <div className="glass-card rounded-xl p-3.5 text-center">
            <div className="text-xs text-slate-400 font-medium">Background Processing</div>
            <div className="text-sm font-semibold text-white mt-1">Python Async Worker</div>
          </div>
          <div className="glass-card rounded-xl p-3.5 text-center">
            <div className="text-xs text-slate-400 font-medium">Client Interface</div>
            <div className="text-sm font-semibold text-white mt-1">React + Vite + Tailwind</div>
          </div>
        </div>
      </div>
    </section>
  );
};

import React from 'react';
import { GitBranch, Github } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/60 py-12 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center">
              <GitBranch className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm text-white">RepoMind</span>
              <p className="text-xs text-slate-500">AI Codebase Intelligence Platform</p>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-xs text-slate-400">
            <a href="#health" className="hover:text-slate-200 transition">Health Status</a>
            <a href="#capabilities" className="hover:text-slate-200 transition">Platform Vision</a>
            <a href="#architecture" className="hover:text-slate-200 transition">Monorepo Topology</a>
            <a
              href="https://github.com/sskb230506/RepoMind"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1.5 hover:text-white transition"
            >
              <Github className="w-3.5 h-3.5" />
              <span>GitHub Repository</span>
            </a>
          </div>

          <div className="text-xs text-slate-500 flex items-center space-x-1">
            <span>Built with precision for developer velocity</span>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-900 text-center text-xs text-slate-600">
          &copy; {new Date().getFullYear()} RepoMind. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

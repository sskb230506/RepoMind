import React from 'react';
import { Network, GitPullRequest, History, CheckCheck, Bot, Database } from 'lucide-react';

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  badge: string;
  badgeColor: string;
  description: string;
  capabilities: string[];
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  badge,
  badgeColor,
  description,
  capabilities,
}) => (
  <div className="glass-card rounded-2xl p-6 border border-slate-800/80 hover:border-purple-500/30 transition duration-300 flex flex-col justify-between group">
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:text-purple-300 transition">
          {icon}
        </div>
        <span className={`text-[10px] uppercase font-semibold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
          {badge}
        </span>
      </div>

      <h3 className="text-base font-semibold text-white tracking-tight mb-2 group-hover:text-purple-200 transition">
        {title}
      </h3>

      <p className="text-xs text-slate-400 leading-relaxed mb-4">
        {description}
      </p>
    </div>

    <div className="pt-4 border-t border-slate-800/80">
      <div className="text-[11px] font-medium text-slate-400 mb-2 uppercase tracking-wider">Capabilities</div>
      <ul className="space-y-1.5">
        {capabilities.map((item, idx) => (
          <li key={idx} className="text-xs text-slate-300 flex items-center space-x-2">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  </div>
);

export const Features: React.FC = () => {
  const features = [
    {
      icon: <Network className="w-5 h-5" />,
      title: "Dependency Tracing",
      badge: "Core Engine",
      badgeColor: "bg-indigo-500/10 text-indigo-300 border-indigo-500/20",
      description: "Synthesize full codebase call graphs, module boundaries, and circular import chains across multiple programming languages.",
      capabilities: ["Module dependency mapping", "Symbol cross-references", "Coupling & cohesion metrics"],
    },
    {
      icon: <GitPullRequest className="w-5 h-5" />,
      title: "Change-Impact Analysis",
      badge: "Precision",
      badgeColor: "bg-purple-500/10 text-purple-300 border-purple-500/20",
      description: "Pinpoint exactly which services, endpoints, and components are affected before merging pull requests.",
      capabilities: ["AST blast-radius calculation", "Breaking API detection", "Risk assessment scores"],
    },
    {
      icon: <History className="w-5 h-5" />,
      title: "Git History Intelligence",
      badge: "Temporal",
      badgeColor: "bg-blue-500/10 text-blue-300 border-blue-500/20",
      description: "Unravel file churn patterns, code ownership dynamics, and architectural regression timelines across Git commits.",
      capabilities: ["Code churn heatmaps", "Author contribution analysis", "Hotspot identification"],
    },
    {
      icon: <CheckCheck className="w-5 h-5" />,
      title: "Test Discovery & Mapping",
      badge: "Quality",
      badgeColor: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
      description: "Automatically map changed functions and modules to their corresponding unit, integration, and E2E test suites.",
      capabilities: ["Targeted test selection", "Coverage gap alerts", "Flaky test correlation"],
    },
    {
      icon: <Database className="w-5 h-5" />,
      title: "Repository Indexing & Ingestion",
      badge: "Asynchronous",
      badgeColor: "bg-amber-500/10 text-amber-300 border-amber-500/20",
      description: "High-performance background workers parse and tokenize repositories into structured relational and graph records.",
      capabilities: ["Python Asyncio workers", "PostgreSQL schema storage", "Incremental commit sync"],
    },
    {
      icon: <Bot className="w-5 h-5" />,
      title: "Agentic Code Validation",
      badge: "Next Phase",
      badgeColor: "bg-pink-500/10 text-pink-300 border-pink-500/20",
      description: "Future milestone: AI agents will propose targeted refactors, bug fixes, and validate modifications directly in sandbox tests.",
      capabilities: ["Autonomous PR proposals", "Sandboxed execution", "Safety guardrail enforcement"],
    },
  ];

  return (
    <section id="capabilities" className="py-16 scroll-mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Codebase Intelligence Pillars
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            Architected to transform opaque code repositories into fully observable, queryable knowledge graphs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <FeatureCard key={idx} {...feature} />
          ))}
        </div>
      </div>
    </section>
  );
};

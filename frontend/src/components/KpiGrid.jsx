import React from 'react';
import {
  Briefcase,
  Award,
  Wallet,
  Gauge,
  Layers,
  CalendarClock,
} from 'lucide-react';

export default function KpiGrid({ kpis }) {
  const safeKpis = kpis || {};

  const cards = [
    {
      label: 'Opportunities Discovered',
      value: safeKpis.opportunities_discovered ?? 0,
      sub: 'Total tailored ideas in workspace',
      icon: Briefcase,
      iconBadge: 'bg-blue-600 text-white shadow-sm',
      borderAccent: 'hover:border-blue-500/50',
    },
    {
      label: 'High-Potential Opportunities',
      value: safeKpis.high_potential_opportunities ?? 0,
      sub: 'Score ≥ 82 / 100 across 5 factors',
      icon: Award,
      iconBadge: 'bg-emerald-600 text-white shadow-sm',
      borderAccent: 'hover:border-emerald-500/50',
    },
    {
      label: 'Estimated Startup Budget Range',
      value: safeKpis.estimated_startup_budget_range || '₹45,000 – ₹4,50,000',
      sub: 'Calibrated to local cost index',
      icon: Wallet,
      iconBadge: 'bg-indigo-600 text-white shadow-sm',
      borderAccent: 'hover:border-indigo-500/50',
    },
    {
      label: 'Average Opportunity Score',
      value: `${safeKpis.average_opportunity_score ?? 84} / 100`,
      sub: 'Weighted 5-factor viability index',
      icon: Gauge,
      iconBadge: 'bg-teal-600 text-white shadow-sm',
      borderAccent: 'hover:border-teal-500/50',
    },
    {
      label: 'Business Categories Analysed',
      value: safeKpis.business_categories_analysed ?? 1,
      sub: 'Everyday retail, food & services',
      icon: Layers,
      iconBadge: 'bg-amber-600 text-white shadow-sm',
      borderAccent: 'hover:border-amber-500/50',
    },
    {
      label: 'Last Analysis Date',
      value: safeKpis.last_analysis_date || 'Just now',
      sub: safeKpis.is_initial_seed
        ? 'Initial baseline batch (Run search to update)'
        : 'Calculated from stored SQLite searches',
      icon: CalendarClock,
      iconBadge: 'bg-slate-600 text-white shadow-sm',
      borderAccent: 'hover:border-slate-500/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div
            key={c.label}
            className={`glass-panel glass-panel-hover p-4 flex flex-col justify-between ${c.borderAccent}`}
          >
            <div className="flex items-center justify-between gap-2 mb-3">
              <span className="text-xs font-bold text-slate-300 leading-tight">
                {c.label}
              </span>
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${c.iconBadge}`}
              >
                <Icon className="w-4 h-4 text-white" strokeWidth={2.2} />
              </div>
            </div>
            <div>
              <div className="text-lg sm:text-xl font-extrabold text-white tracking-tight truncate">
                {c.value}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 truncate" title={c.sub}>
                {c.sub}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

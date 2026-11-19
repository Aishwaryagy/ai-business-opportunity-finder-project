import React from 'react';
import {
  MapPin,
  Wallet,
  TrendingUp,
  Bookmark,
  GitCompare,
  ArrowUpRight,
  CheckCircle2,
} from 'lucide-react';

export default function OpportunityCard({
  opportunity,
  onSelectReport,
  onSaveReport,
  onToggleCompare,
  isCompared = false,
}) {
  if (!opportunity) return null;

  const sb = opportunity.startupBudget || {};
  const fp = opportunity.financialProjections || {};
  const score = opportunity.score || 80;

  const scoreColor =
    score >= 85
      ? 'bg-emerald-600 text-white'
      : score >= 75
      ? 'bg-blue-600 text-white'
      : 'bg-amber-600 text-white';

  // Clean redundant suffixes/prefixes so the card stays concise and engaging
  const cleanTitle = (opportunity.title || '').replace(/\s*\(Proven [^)]+Model\)\s*$/i, '');
  const cleanSummary = (opportunity.summary || '').replace(/^\[[^\]]+\]\s*/i, '');

  const originState = opportunity.crossRegionInsight?.proven_in_state;

  return (
    <div className="glass-panel glass-panel-hover p-5 flex flex-col justify-between gap-4">
      <div>
        {/* Top Row: Essential Badges + Score */}
        <div className="flex items-start justify-between gap-3 mb-2.5">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
              {opportunity.category}
            </span>

            {originState ? (
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/35">
                🌍 Proven in {originState}
              </span>
            ) : (
              opportunity.beginner_friendly && (
                <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Beginner Friendly
                </span>
              )
            )}
          </div>

          <div
            className={`w-12 h-12 rounded-xl ${scoreColor} shadow-sm flex flex-col items-center justify-center shrink-0`}
            title="Opportunity Viability Score (/100)"
          >
            <span className="text-base font-black leading-none">{score}</span>
            <span className="text-[8px] uppercase font-bold tracking-wider opacity-90 mt-0.5">
              Score
            </span>
          </div>
        </div>

        {/* Clean Title */}
        <h3
          onClick={() => onSelectReport(opportunity)}
          className="text-base font-extrabold text-white hover:text-blue-400 cursor-pointer leading-snug transition line-clamp-2 mb-1.5"
        >
          {cleanTitle}
        </h3>

        {/* Compact Location Line */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-2.5">
          <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span className="truncate">
            {opportunity.area}, {opportunity.city}, {opportunity.state}
          </span>
        </div>

        {/* Crisp 2-Line Pitch */}
        <p className="text-xs text-slate-300 leading-relaxed mb-3.5 line-clamp-2">
          {cleanSummary}
        </p>

        {/* Essential Financial Snapshot (Setup Cost + Monthly Profit) */}
        <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-900/75 border border-slate-800/90">
          <div>
            <div className="text-[11px] text-slate-400 flex items-center gap-1">
              <Wallet className="w-3 h-3 text-blue-400" />
              Est. Setup Cost
            </div>
            <div className="text-sm font-extrabold text-white mt-0.5">
              {sb.total_formatted || `${opportunity.currency_symbol || '₹'}2,50,000`}
            </div>
            <div className="text-[10px] text-emerald-400 font-medium">
              {sb.within_budget ? '✓ Within budget' : 'Modular setup'}
            </div>
          </div>

          <div>
            <div className="text-[11px] text-slate-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-400" />
              Est. Monthly Profit
            </div>
            <div className="text-sm font-extrabold text-emerald-400 mt-0.5 truncate">
              {fp.scenarios?.[1]?.monthly_net_profit_formatted ||
                fp.estimated_monthly_net_operating_profit ||
                'View Report'}
              /mo
            </div>
            <div className="text-[10px] text-slate-400">
              Payback: {fp.scenarios?.[1]?.payback_period_label || '~6-9 mos'}
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          {onSaveReport && (
            <button
              type="button"
              onClick={() => onSaveReport(opportunity)}
              title="Bookmark report"
              className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-800 flex items-center gap-1 cursor-pointer transition"
            >
              <Bookmark className="w-3.5 h-3.5 text-blue-400" />
              <span>Save</span>
            </button>
          )}

          {onToggleCompare && (
            <button
              type="button"
              onClick={() => onToggleCompare(opportunity)}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-semibold border flex items-center gap-1 cursor-pointer transition ${
                isCompared
                  ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                  : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300'
              }`}
            >
              <GitCompare className="w-3.5 h-3.5 text-blue-400" />
              <span>{isCompared ? 'Compared' : 'Compare'}</span>
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={() => onSelectReport(opportunity)}
          className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm cursor-pointer transition"
        >
          <span>Full Report</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

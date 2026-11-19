import React from 'react';
import {
  Cpu,
  Radio,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import DiscoveryForm from '../components/DiscoveryForm';
import OpportunityCard from '../components/OpportunityCard';

export default function DiscoverPage({
  countries,
  categoriesData,
  onDiscover,
  isLoading,
  error,
  discoveryResult,
  onSelectOpportunity,
  onSaveReport,
  onToggleCompare,
  compareIds = [],
}) {
  const nlp = discoveryResult?.nlp_summary;
  const opportunities = discoveryResult?.opportunities || [];

  return (
    <div className="space-y-6">
      {/* Guided Discovery Form */}
      <DiscoveryForm
        countries={countries}
        categoriesData={categoriesData}
        onSubmit={onDiscover}
        isLoading={isLoading}
      />

      {error && (
        <div className="glass-panel p-4 border border-red-500/30 bg-red-500/10 text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Discovery Results Section */}
      {discoveryResult && (
        <div className="space-y-6">
          {/* NLP & Market Intelligence Evidence Summary */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-blue-500 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5" />
                  Market Intelligence &amp; VADER NLP Synthesis
                </span>
                <h2 className="text-lg sm:text-xl font-bold text-white mt-0.5">
                  Opportunities for {discoveryResult.area}, {discoveryResult.city},{' '}
                  {discoveryResult.state} ({discoveryResult.country})
                </h2>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold flex items-center gap-1.5">
                  <Radio className="w-3.5 h-3.5" />
                  {discoveryResult.data_status_label}
                </span>
                <span className="px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-200 text-xs font-semibold">
                  Capital: {discoveryResult.budget_formatted}
                  {discoveryResult.converted_budget
                    ? ` (≈ ${discoveryResult.converted_budget.converted_formatted})`
                    : ''}
                </span>
              </div>
            </div>

            {/* Observed Evidence vs AI Interpretation Split */}
            {nlp && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 text-xs leading-relaxed text-slate-300">
                  <div className="font-semibold text-blue-400 mb-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Observed Market Evidence ({nlp.records_analysed} Records &bull; {nlp.date_range})
                  </div>
                  <p>{nlp.observed_evidence_summary}</p>
                </div>

                <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 text-xs leading-relaxed text-slate-300">
                  <div className="font-semibold text-indigo-400 mb-1 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" />
                    NLP Theme &amp; Market Gap Synthesis ({nlp.overall_sentiment_label})
                  </div>
                  <p>{nlp.ai_interpretation_summary}</p>
                </div>
              </div>
            )}

            {/* Currency Conversion Note if active */}
            {discoveryResult.converted_budget && (
              <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/25 text-xs text-blue-300">
                <strong>Currency Conversion Applied:</strong>{' '}
                {discoveryResult.converted_budget.explanation}
              </div>
            )}
          </div>

          {/* Opportunities Cards Grid */}
          <div>
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
              <h3 className="text-base font-bold text-white">
                Recommended Business Opportunities ({opportunities.length})
              </h3>
              <span className="text-xs text-slate-400">
                Select <strong>View Full Report</strong> on any card to inspect itemized budgets, financial scenarios &amp; PDF export
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {opportunities.map((opp) => (
                <OpportunityCard
                  key={opp.id}
                  opportunity={opp}
                  onSelectReport={onSelectOpportunity}
                  onSaveReport={onSaveReport}
                  onToggleCompare={onToggleCompare}
                  isCompared={compareIds.includes(opp.id)}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

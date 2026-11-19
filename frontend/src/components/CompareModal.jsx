import React from 'react';
import { X, GitCompare } from 'lucide-react';

export default function CompareModal({
  opportunities = [],
  onClose,
  onRemoveFromCompare,
  onSelectOpportunity,
}) {
  if (!opportunities || opportunities.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-6xl max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-blue-600/15 border border-blue-500/25 flex items-center justify-center text-blue-400">
              <GitCompare className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                Side-by-Side Opportunity Comparison ({opportunities.length})
              </h2>
              <p className="text-xs text-slate-400">
                Compare startup capital, monthly net operating profits, payback timelines, and 5-factor scores
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 cursor-pointer transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-3 px-4 font-semibold w-48">Metric / Factor</th>
                {opportunities.map((opp) => (
                  <th key={opp.id} className="py-3 px-4 min-w-[230px]">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-bold text-white">{opp.title}</span>
                      <button
                        type="button"
                        onClick={() => onRemoveFromCompare(opp.id)}
                        className="text-slate-500 hover:text-red-400 text-xs cursor-pointer"
                        title="Remove from comparison"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="text-[11px] text-blue-400 font-normal mt-0.5">
                      {opp.area}, {opp.city} ({opp.country})
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70 text-slate-200">
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Viability Score</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4 font-bold text-emerald-400 text-base">
                    {opp.score} / 100
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Sector &amp; Format</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4">
                    <div className="font-medium text-white">{opp.category}</div>
                    <div className="text-xs text-slate-400">{opp.business_type}</div>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Est. Startup Capital</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4 font-bold text-blue-400">
                    {opp.startupBudget?.total_formatted}
                    <div className="text-[11px] font-normal text-slate-400">
                      {opp.startupBudget?.within_budget ? '✓ Within Budget' : 'Above Target Budget'}
                    </div>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Base Monthly Revenue</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4">
                    {opp.financialProjections?.scenarios?.[1]?.monthly_revenue_formatted ||
                      opp.financialProjections?.expected_monthly_revenue_range}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Base Monthly Net Profit</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4 font-bold text-emerald-400">
                    {opp.financialProjections?.scenarios?.[1]?.monthly_net_profit_formatted ||
                      opp.financialProjections?.estimated_monthly_net_operating_profit}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Est. Payback Period</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4">
                    {opp.financialProjections?.scenarios?.[1]?.payback_period_label ||
                      opp.financialProjections?.approximate_payback_period}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">5-Factor Breakdown</td>
                {opportunities.map((opp) => {
                  const sb = opp.scoreBreakdown || {};
                  return (
                    <td key={opp.id} className="py-3 px-4 text-xs space-y-1">
                      <div>Customer Need: <strong>{sb.customerNeed}/100</strong></div>
                      <div>Market Demand: <strong>{sb.marketDemand}/100</strong></div>
                      <div>Competition Gap: <strong>{sb.competition}/100</strong></div>
                      <div>Growth Potential: <strong>{sb.growthPotential}/100</strong></div>
                      <div>Budget Feasibility: <strong>{sb.feasibility}/100</strong></div>
                    </td>
                  );
                })}
              </tr>
              <tr>
                <td className="py-3 px-4 font-semibold text-slate-400">Action</td>
                {opportunities.map((opp) => (
                  <td key={opp.id} className="py-3 px-4">
                    <button
                      type="button"
                      onClick={() => {
                        onClose();
                        onSelectOpportunity(opp);
                      }}
                      className="btn-primary-text px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold cursor-pointer transition"
                    >
                      <span className="text-white">Open Full Report &rarr;</span>
                    </button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

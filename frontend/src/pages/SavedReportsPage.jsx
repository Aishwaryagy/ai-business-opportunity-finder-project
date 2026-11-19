import React from 'react';
import {
  BookmarkCheck,
  Trash2,
  Download,
  GitCompare,
  ArrowUpRight,
  Clock,
  Compass,
} from 'lucide-react';
import { downloadOpportunityPdf } from '../services/api';

export default function SavedReportsPage({
  savedReports = [],
  onSelectOpportunity,
  onDeleteSavedReport,
  onToggleCompare,
  compareIds = [],
  onNavigateDiscover,
}) {
  return (
    <div className="space-y-6">
      {/* Saved Reports Section */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2 tracking-tight">
              <BookmarkCheck className="w-5 h-5 text-blue-400" />
              Saved Opportunity Reports ({savedReports.length})
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Bookmarked business opportunity reports archived in your workspace database
            </p>
          </div>
          <button
            type="button"
            onClick={onNavigateDiscover}
            className="btn-primary-text px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-1.5 cursor-pointer transition shadow-sm"
          >
            <Compass className="w-4 h-4 text-white" />
            <span className="text-white">Discover More Opportunities</span>
          </button>
        </div>

        {savedReports.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl">
            <p className="text-sm font-semibold text-slate-300">No saved reports yet</p>
            <p className="text-xs text-slate-400 mt-1">
              Select <strong>Save</strong> on any opportunity card or full report to bookmark it here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {savedReports.map((item) => {
              const opp = item.opportunity || {};
              const isComp = compareIds.includes(opp.id);
              return (
                <div
                  key={item.id}
                  className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between gap-4 hover:border-slate-700 transition"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          {item.category}
                        </span>
                        <h3 className="text-base font-bold text-white mt-2">
                          {item.title}
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {item.area}, {item.city}, {item.state} ({item.country}) &bull;{' '}
                          {opp.startupBudget?.total_formatted}
                        </p>
                      </div>
                      <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 font-bold text-xs">
                        {item.score}/100
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-800">
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => onToggleCompare(opp)}
                        className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1 cursor-pointer transition ${
                          isComp
                            ? 'bg-blue-600/15 border-blue-500/40 text-blue-400'
                            : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <GitCompare className="w-3.5 h-3.5" />
                        <span>{isComp ? 'Compared' : 'Compare'}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => downloadOpportunityPdf(opp)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-300 border border-slate-800 flex items-center gap-1 cursor-pointer transition"
                      >
                        <Download className="w-3.5 h-3.5 text-blue-400" />
                        <span>PDF</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => onDeleteSavedReport(item.id)}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-red-500/15 text-slate-400 hover:text-red-400 border border-slate-800 cursor-pointer transition"
                        title="Delete saved report"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={() => onSelectOpportunity(opp)}
                      className="btn-primary-text px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1 cursor-pointer transition"
                    >
                      <span className="text-white">Open Report</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-white" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

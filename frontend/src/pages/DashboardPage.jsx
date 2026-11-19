import React, { useState } from 'react';
import {
  Sparkles,
  Flame,
  UserCheck,
  Wallet,
  ShoppingBag,
  MapPin,
  Clock,
  Bookmark,
  ArrowRight,
  Search,
  X,
} from 'lucide-react';
import KpiGrid from '../components/KpiGrid';
import DashboardCharts from '../components/DashboardCharts';
import OpportunityCard from '../components/OpportunityCard';
import ReportAssistantPanel from '../components/ReportAssistantPanel';

export default function DashboardPage({
  dashboardData,
  onNavigate,
  onSelectOpportunity,
  onSaveReport,
  onToggleCompare,
  compareIds = [],
  onSelectHistorySearch,
}) {
  const [discoveryTab, setDiscoveryTab] = useState('everyday');
  const [searchQuery, setSearchQuery] = useState('');

  if (!dashboardData) {
    return (
      <div className="glass-panel p-12 text-center">
        <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm font-bold text-slate-200">
          Loading Global Opportunity Intelligence Dashboard...
        </p>
      </div>
    );
  }

  const {
    kpis,
    charts,
    recent_opportunities: allOpps = [],
    saved_reports: savedReports = [],
  } = dashboardData;

  // Filter opportunities by discovery area tab and quick search query
  const filteredOpps = allOpps.filter((o) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchText = [
        o.title,
        o.category,
        o.summary,
        o.city,
        o.state,
        o.area,
        o.crossRegionInsight?.proven_in_state,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      if (!matchText.includes(q)) return false;
    }
    if (discoveryTab === 'everyday') return o.is_everyday_business !== false;
    if (discoveryTab === 'beginner') return o.beginner_friendly !== false;
    if (discoveryTab === 'low_budget') {
      const cap = o.startupBudget?.total_estimated_initial_investment || 0;
      const usr = o.startupBudget?.user_available_budget || 500000;
      return cap <= usr * 0.85;
    }
    if (discoveryTab === 'underserved') return (o.competitionScore || 78) >= 76;
    if (discoveryTab === 'trending') return (o.score || 80) >= 84;
    return true;
  });

  const displayOpps = filteredOpps.length > 0 ? filteredOpps : allOpps;
  const featuredOpportunity = displayOpps[0] || allOpps[0];

  const discoveryTabs = [
    { id: 'everyday', label: 'Everyday-Need Businesses', icon: ShoppingBag },
    { id: 'beginner', label: 'Beginner-Friendly Opportunities', icon: UserCheck },
    { id: 'low_budget', label: 'Low-Budget Businesses', icon: Wallet },
    { id: 'trending', label: 'High-Viability Suggested Ideas', icon: Flame },
    { id: 'underserved', label: 'Underserved Local Markets', icon: MapPin },
    { id: 'recent', label: 'Recently Analysed', icon: Clock },
  ];

  return (
    <div className="space-y-4">
      {/* B. 6 Live KPI Cards */}
      <KpiGrid kpis={kpis} />

      {/* C. Interactive Charts Preview Button */}
      <DashboardCharts charts={charts} />

      {/* D, E, F: Discovery Area + Saved Reports / Recent Searches + AI Report Assistant */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        {/* Left 8 Columns: Discovery Tabs & Opportunity Cards */}
        <div className="xl:col-span-8 space-y-4">
          <div className="glass-panel p-4 space-y-3">
            {/* Title/Subtitle Texts + Immediate Search Bar Right Next / Below */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  Opportunity Discovery Matrix
                </h2>
                <p className="text-xs text-slate-400">
                  Filter practical business recommendations by capital intensity, experience &amp; local gap
                </p>
              </div>

              {/* Search Bar Placed Immediately Next / Below the Texts */}
              <div className="relative w-full sm:w-72 shrink-0">
                <Search className="w-3.5 h-3.5 text-blue-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search ideas, states, or category..."
                  className="w-full pl-8 pr-8 py-2 rounded-xl bg-slate-950/90 border border-slate-700 text-xs text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1 border-t border-slate-800/80">
              {discoveryTabs.map((t) => {
                const Icon = t.icon;
                const active = discoveryTab === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setDiscoveryTab(t.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                      active
                        ? 'bg-blue-600 text-white border border-blue-500 shadow-sm'
                        : 'bg-slate-900/70 text-slate-400 hover:text-white border border-slate-800'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {displayOpps.slice(0, 4).map((opp) => (
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

        {/* Right 4 Columns: AI Assistant Panel + Saved Reports & Recent Searches */}
        <div className="xl:col-span-4 space-y-6">
          {/* F. Interactive Report Assistant Panel */}
          <ReportAssistantPanel opportunity={featuredOpportunity} />

          {/* E. Saved Reports & Search Summary */}
          <div className="glass-panel p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Bookmark className="w-4 h-4 text-blue-400" />
                Saved Reports
              </h3>
              <button
                type="button"
                onClick={() => onNavigate('saved')}
                className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 cursor-pointer"
              >
                <span>View All</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* Saved Reports List */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                Bookmarked Reports ({savedReports.length})
              </div>
              {savedReports.length === 0 ? (
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
                  No reports bookmarked yet. Click <strong>Save</strong> on any opportunity card to
                  bookmark it in your library.
                </div>
              ) : (
                <div className="space-y-2">
                  {savedReports.slice(0, 3).map((sr) => (
                    <div
                      key={sr.id}
                      onClick={() => onSelectOpportunity(sr.opportunity)}
                      className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 flex items-center justify-between gap-2 cursor-pointer transition"
                    >
                      <div className="truncate">
                        <div className="text-xs font-bold text-white truncate">{sr.title}</div>
                        <div className="text-[11px] text-slate-400">
                          {sr.area}, {sr.city} &bull; {sr.category}
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs font-bold shrink-0">
                        {sr.score}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Summary Link to Dedicated Search History Page */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>
                  Total Recorded Searches:{' '}
                  <strong className="text-white">{kpis?.total_searches ?? 0}</strong>
                </span>
              </div>
              <button
                type="button"
                onClick={() => onNavigate('history')}
                className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 cursor-pointer shrink-0"
              >
                <span>Open History</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

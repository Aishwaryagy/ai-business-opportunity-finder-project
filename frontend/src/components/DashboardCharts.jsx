import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  RadialBarChart,
  RadialBar,
  AreaChart,
  Area,
  ComposedChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import {
  PieChart as PieIcon,
  TrendingUp,
  Wallet,
  Activity,
  DollarSign,
  Info,
  Sparkles,
  X,
  Eye,
} from 'lucide-react';

// Professional SaaS Business Intelligence Palette
const SAAS_PALETTE = [
  '#2563EB', // Primary Royal Blue
  '#0D9488', // Executive Teal
  '#4F46E5', // Deep Indigo
  '#16A34A', // Success Green
  '#D97706', // Warning Amber
  '#0284C7', // Sky Blue
  '#DC2626', // Danger Red
  '#475569', // Slate Secondary
];

const BUDGET_DONUT_COLORS = [
  '#2563EB', // Primary Blue
  '#4F46E5', // Indigo
  '#0D9488', // Teal
  '#16A34A', // Green
  '#D97706', // Amber
  '#475569', // Slate
];

const darkTooltipStyle = {
  backgroundColor: '#1E293B',
  border: '1px solid #334155',
  borderRadius: '12px',
  color: '#F8FAFC',
  fontSize: '12px',
  boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.5)',
};

const shortLabel = (str = '', max = 16) =>
  str.length > max ? `${str.slice(0, max)}…` : str;

export default function DashboardCharts({ charts }) {
  // Charts are hidden by default; only displayed when user clicks the centered preview button
  const [isOpen, setIsOpen] = useState(false);
  const [studioFilter, setStudioFilter] = useState('all'); // 'all' | 'donut' | 'radar' | 'wave' | 'trends'

  // Per-card chart style switcher inside the studio
  const [budgetView, setBudgetView] = useState('donut'); // 'donut' | 'radial' | 'bar'
  const [demandView, setDemandView] = useState('radar'); // 'radar' | 'pie' | 'composed'
  const [revenueView, setRevenueView] = useState('wave'); // 'wave' | 'donut' | 'bar'

  // Allow closing with Escape key
  useEffect(() => {
    if (!isOpen) return undefined;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const safeCharts = charts || {};

  const categoryData = (safeCharts.category_distribution || []).map((item, idx) => ({
    ...item,
    fill: SAAS_PALETTE[idx % SAAS_PALETTE.length],
  }));

  const historyData = safeCharts.historical_trends || [];
  const hasHistorical = Boolean(safeCharts.has_historical_data && historyData.length > 0);

  const finData = (safeCharts.financial_and_demand_comparison || []).map((item, idx) => ({
    ...item,
    shortName: shortLabel(item.name || `Idea ${idx + 1}`, 15),
    fill: BUDGET_DONUT_COLORS[idx % BUDGET_DONUT_COLORS.length],
  }));

  const totalCapex = finData.reduce((acc, d) => acc + (Number(d.startupCapex) || 0), 0);
  const totalMonthlyProfit = finData.reduce(
    (acc, d) => acc + (Number(d.monthlyNetProfit) || 0),
    0
  );

  const studioTabs = [
    { id: 'all', label: '⚡ All 5 Visuals' },
    { id: 'donut', label: '🍩 Donut & CapEx' },
    { id: 'radar', label: '🕸️ 360° Demand Radar' },
    { id: 'wave', label: '🌊 Profit Wave' },
    { id: 'trends', label: '📈 Category & Score' },
  ];

  return (
    <>
      {/* Centered Interactive Preview Trigger Bar with Generous Breathing Space */}
      <div className="flex justify-center py-2 no-print">
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group relative inline-flex items-center gap-3 p-[1px] rounded-2xl bg-slate-700/80 hover:bg-blue-600 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer"
        >
          <div className="flex items-center gap-3.5 px-5 py-3 rounded-[15px] bg-slate-900">
            {/* Mini Donut + Bars Preview Badge */}
            <div className="relative w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-sm">
              <PieIcon className="w-4 h-4 text-white" strokeWidth={2.2} />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-slate-900" />
            </div>

            <div className="text-left">
              <div className="flex items-center gap-2">
                <span className="text-xs sm:text-sm font-bold text-white">
                  Visual Charts Studio
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-600 text-white">
                  5 Live
                </span>
              </div>
              <div className="text-[11px] font-medium text-slate-400 flex items-center gap-1 mt-0.5">
                <span>Tap to preview Donut, 360&deg; Radar &amp; Profit Waves</span>
              </div>
            </div>

            {/* Mini Live Equalizer Bars Preview Icon */}
            <div className="flex items-end gap-0.5 h-5 px-2 py-1 rounded-lg bg-slate-950 border border-slate-800">
              <span className="w-1 h-2.5 rounded-full bg-blue-500 group-hover:h-3.5 transition-all" />
              <span className="w-1 h-3.5 rounded-full bg-indigo-500 group-hover:h-2 transition-all" />
              <span className="w-1 h-2 rounded-full bg-emerald-500 group-hover:h-3.5 transition-all" />
              <span className="w-1 h-3 rounded-full bg-amber-500 group-hover:h-2.5 transition-all" />
            </div>

            <span className="w-8 h-8 rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center shadow-sm group-hover:translate-x-0.5 transition-transform">
              <Eye className="w-4 h-4 text-white" strokeWidth={2.2} />
            </span>
          </div>
        </button>
      </div>

      {/* Interactive Visual Charts Studio Modal / Drawer */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-end bg-slate-950/75 backdrop-blur-sm p-2 sm:p-5 animate-fadeIn no-print"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsOpen(false);
          }}
        >
          <div className="relative w-full max-w-6xl max-h-[92vh] overflow-y-auto rounded-2xl bg-[#0F172A] border border-slate-700 shadow-2xl p-5 sm:p-7 space-y-6">
            {/* Top Header Bar inside the Studio */}
            <div className="sticky top-0 z-20 -mx-5 -mt-5 sm:-mx-7 sm:-mt-7 px-5 py-4 sm:px-7 bg-[#0F172A]/95 backdrop-blur-md border-b border-slate-800 flex flex-wrap items-center justify-between gap-4 rounded-t-2xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm">
                  <Sparkles className="w-5 h-5 text-white" strokeWidth={2.2} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base sm:text-lg font-bold tracking-tight text-white">
                      Interactive Visual Analytics Studio
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-blue-500/15 text-blue-400 border border-blue-500/30">
                      Analytics Suite
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Explore multi-ring donuts, 360&deg; spider radars, radial gauges &amp; profit waves on demand
                  </p>
                </div>
              </div>

              {/* Quick Filter Pills + Close Button */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex flex-wrap items-center gap-1.5 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
                  {studioTabs.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setStudioFilter(t.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        studioFilter === t.id
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  title="Close Visual Studio (Esc)"
                  className="p-2.5 rounded-xl bg-slate-800 hover:bg-red-600 text-slate-300 hover:text-white border border-slate-700 cursor-pointer transition"
                >
                  <X className="w-4 h-4" strokeWidth={2.2} />
                </button>
              </div>
            </div>

            {/* Row 1: Category Multi-Ring Donut + Score Trajectory Spline */}
            {(studioFilter === 'all' || studioFilter === 'trends' || studioFilter === 'donut') && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Chart 1: Multi-Ring Donut & Pie Chart — Category Distribution */}
                <div className="glass-panel p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2.5">
                      <span className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
                        <PieIcon className="w-4 h-4 text-white" strokeWidth={2.2} />
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          Opportunity Share by Category
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Outer Donut: Idea Count &bull; Inner Pie: Avg Score (/100)
                        </p>
                      </div>
                    </div>
                    <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
                      Multi-Ring Donut
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-12 items-center gap-4">
                    <div className="sm:col-span-7 h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <defs>
                            <linearGradient id="catGrad0" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#3B82F6" />
                              <stop offset="100%" stopColor="#1D4ED8" />
                            </linearGradient>
                            <linearGradient id="catGrad1" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#14B8A6" />
                              <stop offset="100%" stopColor="#0F766E" />
                            </linearGradient>
                            <linearGradient id="catGrad2" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#6366F1" />
                              <stop offset="100%" stopColor="#4338CA" />
                            </linearGradient>
                            <linearGradient id="catGrad3" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#22C55E" />
                              <stop offset="100%" stopColor="#15803D" />
                            </linearGradient>
                            <linearGradient id="catGrad4" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#F59E0B" />
                              <stop offset="100%" stopColor="#B45309" />
                            </linearGradient>
                            <linearGradient id="catGrad5" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#64748B" />
                              <stop offset="100%" stopColor="#334155" />
                            </linearGradient>
                          </defs>
                          <Tooltip
                            contentStyle={darkTooltipStyle}
                            itemStyle={{ color: '#F8FAFC', fontWeight: 600 }}
                          />
                          <Pie
                            data={categoryData}
                            dataKey="avgScore"
                            nameKey="category"
                            cx="50%"
                            cy="50%"
                            innerRadius={22}
                            outerRadius={52}
                            paddingAngle={3}
                            cornerRadius={5}
                            stroke="rgba(15, 23, 42, 0.6)"
                            strokeWidth={2}
                          >
                            {categoryData.map((_, idx) => (
                              <Cell
                                key={`inner-${idx}`}
                                fill={SAAS_PALETTE[(idx + 2) % SAAS_PALETTE.length]}
                                fillOpacity={0.85}
                              />
                            ))}
                          </Pie>
                          <Pie
                            data={categoryData}
                            dataKey="count"
                            nameKey="category"
                            cx="50%"
                            cy="50%"
                            innerRadius={64}
                            outerRadius={94}
                            paddingAngle={4}
                            cornerRadius={7}
                            stroke="rgba(15, 23, 42, 0.7)"
                            strokeWidth={2}
                            label={({ percent }) => `${Math.round((percent || 0) * 100)}%`}
                            labelLine={false}
                          >
                            {categoryData.map((_, idx) => (
                              <Cell key={`outer-${idx}`} fill={`url(#catGrad${idx % 6})`} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="sm:col-span-5 space-y-2 pr-2">
                      {categoryData.map((cat, idx) => (
                        <div
                          key={cat.category || idx}
                          className="flex items-center justify-between px-3 py-2 rounded-xl bg-slate-900 border border-slate-800"
                        >
                          <div className="flex items-center gap-2 truncate">
                            <span
                              className="w-3 h-3 rounded-full shrink-0"
                              style={{ backgroundColor: SAAS_PALETTE[idx % SAAS_PALETTE.length] }}
                            />
                            <span className="text-xs font-semibold text-slate-200 truncate">
                              {cat.category}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[11px] font-semibold text-blue-400">
                              {cat.count} {cat.count === 1 ? 'idea' : 'ideas'}
                            </span>
                            <span className="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                              {cat.avgScore}/100
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Chart 2: Opportunity Trends Over Time */}
                <div className="glass-panel p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2.5">
                      <span className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
                        <TrendingUp className="w-4 h-4 text-white" strokeWidth={2.2} />
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          Opportunity Score Trajectory
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Tracks viability scores across stored discovery sessions
                        </p>
                      </div>
                    </div>
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${
                        hasHistorical
                          ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                          : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                      }`}
                    >
                      {hasHistorical ? `${historyData.length} Stored Searches` : 'Live Session'}
                    </span>
                  </div>

                  {hasHistorical ? (
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                          data={historyData}
                          margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                        >
                          <defs>
                            <linearGradient id="saasBlueGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#2563EB" stopOpacity={0.45} />
                              <stop offset="55%" stopColor="#3B82F6" stopOpacity={0.2} />
                              <stop offset="95%" stopColor="#60A5FA" stopOpacity={0.02} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.16)" />
                          <XAxis dataKey="searchLabel" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                          <YAxis domain={[40, 100]} stroke="#94A3B8" tick={{ fontSize: 11 }} />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '12px' }} />
                          <Area
                            type="monotone"
                            dataKey="avgScore"
                            name="Average Opportunity Score (/100)"
                            stroke="#3B82F6"
                            strokeWidth={2.5}
                            fillOpacity={1}
                            fill="url(#saasBlueGrad)"
                            dot={{ r: 4, fill: '#60A5FA', stroke: '#1D4ED8', strokeWidth: 2 }}
                            activeDot={{ r: 6, fill: '#2563EB', stroke: '#FFFFFF', strokeWidth: 2 }}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-64 flex flex-col items-center justify-center text-center px-6 border border-dashed border-slate-800 rounded-xl bg-slate-900/40">
                      <Info className="w-8 h-8 text-amber-500 mb-2" />
                      <h4 className="text-sm font-bold text-slate-200">
                        No Historical Search Series Recorded Yet
                      </h4>
                      <p className="text-xs text-slate-400 max-w-md mt-1">
                        Run one or more searches in{' '}
                        <strong className="text-blue-400">Discover Opportunities</strong> to
                        populate your historical trajectory here.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Row 2: 3 Visual Charts (Donut Ring + Spider Radar + Multi-Wave Spline) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Chart 3: Startup Budget Comparison */}
              {(studioFilter === 'all' || studioFilter === 'donut') && (
                <div className="glass-panel p-5 flex flex-col justify-between">
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm shrink-0">
                        <Wallet className="w-4 h-4 text-white" strokeWidth={2.2} />
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-white">Startup Budget Comparison</h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Initial setup CapEx share across ideas
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 shrink-0">
                      {[
                        { id: 'donut', label: 'Donut' },
                        { id: 'radial', label: 'Radial' },
                        { id: 'bar', label: 'Bar' },
                      ].map((m) => (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => setBudgetView(m.id)}
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                            budgetView === m.id
                              ? 'bg-blue-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="h-60 w-full relative">
                    {budgetView === 'donut' && (
                      <>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <defs>
                              <linearGradient id="budGrad0" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stopColor="#3B82F6" />
                                <stop offset="100%" stopColor="#1D4ED8" />
                              </linearGradient>
                              <linearGradient id="budGrad1" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stopColor="#6366F1" />
                                <stop offset="100%" stopColor="#4338CA" />
                              </linearGradient>
                              <linearGradient id="budGrad2" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stopColor="#14B8A6" />
                                <stop offset="100%" stopColor="#0F766E" />
                              </linearGradient>
                              <linearGradient id="budGrad3" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stopColor="#22C55E" />
                                <stop offset="100%" stopColor="#15803D" />
                              </linearGradient>
                              <linearGradient id="budGrad4" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stopColor="#F59E0B" />
                                <stop offset="100%" stopColor="#B45309" />
                              </linearGradient>
                              <linearGradient id="budGrad5" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stopColor="#64748B" />
                                <stop offset="100%" stopColor="#334155" />
                              </linearGradient>
                            </defs>
                            <Tooltip
                              contentStyle={darkTooltipStyle}
                              formatter={(value, name) => [
                                Number(value || 0).toLocaleString(),
                                name === 'startupCapex' ? 'Est. Initial Setup' : name,
                              ]}
                            />
                            <Legend
                              wrapperStyle={{ fontSize: '11px' }}
                              formatter={(val) => shortLabel(val, 18)}
                            />
                            <Pie
                              data={finData}
                              dataKey="startupCapex"
                              nameKey="shortName"
                              cx="50%"
                              cy="45%"
                              innerRadius={52}
                              outerRadius={82}
                              paddingAngle={5}
                              cornerRadius={8}
                              stroke="rgba(15, 23, 42, 0.55)"
                              strokeWidth={2}
                            >
                              {finData.map((_, idx) => (
                                <Cell key={`bud-donut-${idx}`} fill={`url(#budGrad${idx % 6})`} />
                              ))}
                            </Pie>
                          </PieChart>
                        </ResponsiveContainer>
                        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center -translate-y-3">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                            Avg CapEx
                          </span>
                          <span className="text-xs font-extrabold text-blue-400">
                            {finData.length > 0
                              ? Math.round(totalCapex / finData.length).toLocaleString()
                              : '—'}
                          </span>
                        </div>
                      </>
                    )}

                    {budgetView === 'radial' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <RadialBarChart
                          cx="50%"
                          cy="50%"
                          innerRadius="20%"
                          outerRadius="92%"
                          barSize={12}
                          data={finData}
                        >
                          <RadialBar
                            minAngle={15}
                            background={{ fill: 'rgba(148, 163, 184, 0.12)' }}
                            clockWise
                            dataKey="startupCapex"
                            cornerRadius={8}
                          />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend
                            iconSize={9}
                            layout="horizontal"
                            verticalAlign="bottom"
                            wrapperStyle={{ fontSize: '10px' }}
                          />
                        </RadialBarChart>
                      </ResponsiveContainer>
                    )}

                    {budgetView === 'bar' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={finData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.16)" />
                          <XAxis dataKey="shortName" stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <YAxis stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px' }} />
                          <Bar
                            dataKey="startupCapex"
                            name="Est. Initial Setup"
                            fill="#2563EB"
                            radius={[6, 6, 0, 0]}
                          />
                          <Bar
                            dataKey="userBudget"
                            name="Available Budget"
                            fill="#64748B"
                            radius={[6, 6, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>
              )}

              {/* Chart 4: Market Demand vs. Competition Room */}
              {(studioFilter === 'all' || studioFilter === 'radar') && (
                <div className="glass-panel p-5 flex flex-col justify-between">
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white shadow-sm shrink-0">
                        <Activity className="w-4 h-4 text-white" strokeWidth={2.2} />
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          Market Demand vs. Competition
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          360&deg; Radar: Demand vs. competitive gap (/100)
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 shrink-0">
                      {[
                        { id: 'radar', label: 'Radar' },
                        { id: 'pie', label: 'Pie' },
                        { id: 'composed', label: 'Combo' },
                      ].map((m) => (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => setDemandView(m.id)}
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                            demandView === m.id
                              ? 'bg-teal-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="h-60 w-full relative">
                    {demandView === 'radar' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="72%" data={finData}>
                          <defs>
                            <linearGradient id="radarDemandGrad" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#2563EB" stopOpacity={0.55} />
                              <stop offset="100%" stopColor="#0D9488" stopOpacity={0.3} />
                            </linearGradient>
                            <linearGradient id="radarCompGrad" x1="0" y1="0" x2="1" y2="1">
                              <stop offset="0%" stopColor="#D97706" stopOpacity={0.5} />
                              <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.25} />
                            </linearGradient>
                          </defs>
                          <PolarGrid stroke="rgba(148, 163, 184, 0.22)" />
                          <PolarAngleAxis
                            dataKey="shortName"
                            tick={{ fill: '#94A3B8', fontSize: 10, fontWeight: 600 }}
                          />
                          <PolarRadiusAxis
                            angle={30}
                            domain={[0, 100]}
                            tick={{ fill: '#64748B', fontSize: 9 }}
                          />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px' }} />
                          <Radar
                            name="Market Demand (/100)"
                            dataKey="demandScore"
                            stroke="#3B82F6"
                            strokeWidth={2}
                            fill="url(#radarDemandGrad)"
                            fillOpacity={0.75}
                          />
                          <Radar
                            name="Competitive Gap (/100)"
                            dataKey="competitionScore"
                            stroke="#D97706"
                            strokeWidth={2}
                            fill="url(#radarCompGrad)"
                            fillOpacity={0.65}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    )}

                    {demandView === 'pie' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px' }} />
                          <Pie
                            data={finData}
                            dataKey="demandScore"
                            nameKey="shortName"
                            cx="50%"
                            cy="46%"
                            innerRadius={28}
                            outerRadius={78}
                            paddingAngle={4}
                            cornerRadius={6}
                            label={({ value }) => `${value}%`}
                            labelLine={false}
                          >
                            {finData.map((_, idx) => (
                              <Cell
                                key={`dem-pie-${idx}`}
                                fill={SAAS_PALETTE[idx % SAAS_PALETTE.length]}
                              />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    )}

                    {demandView === 'composed' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart
                          data={finData}
                          margin={{ top: 10, right: 10, left: 0, bottom: 10 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.16)" />
                          <XAxis dataKey="shortName" stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <YAxis domain={[0, 100]} stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px' }} />
                          <Bar
                            dataKey="demandScore"
                            name="Market Demand (/100)"
                            fill="#0D9488"
                            radius={[5, 5, 0, 0]}
                          />
                          <Line
                            type="monotone"
                            dataKey="competitionScore"
                            name="Competitive Gap (/100)"
                            stroke="#D97706"
                            strokeWidth={2.5}
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>
              )}

              {/* Chart 5: Base Monthly Revenue vs. Operating Costs */}
              {(studioFilter === 'all' || studioFilter === 'wave') && (
                <div className="glass-panel p-5 flex flex-col justify-between">
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm shrink-0">
                        <DollarSign className="w-4 h-4 text-white" strokeWidth={2.2} />
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          Revenue vs. Operating Costs
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Monthly sales, operating costs &amp; net profit wave
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 shrink-0">
                      {[
                        { id: 'wave', label: 'Wave' },
                        { id: 'donut', label: 'Donut' },
                        { id: 'bar', label: 'Bar' },
                      ].map((m) => (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => setRevenueView(m.id)}
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                            revenueView === m.id
                              ? 'bg-emerald-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="h-60 w-full relative">
                    {revenueView === 'wave' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart
                          data={finData}
                          margin={{ top: 10, right: 10, left: 0, bottom: 10 }}
                        >
                          <defs>
                            <linearGradient id="revWaveGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#2563EB" stopOpacity={0.45} />
                              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.05} />
                            </linearGradient>
                            <linearGradient id="costWaveGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#D97706" stopOpacity={0.4} />
                              <stop offset="95%" stopColor="#D97706" stopOpacity={0.04} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.16)" />
                          <XAxis dataKey="shortName" stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <YAxis stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px' }} />
                          <Area
                            type="monotone"
                            dataKey="monthlyRevenue"
                            name="Est. Monthly Revenue"
                            stroke="#3B82F6"
                            strokeWidth={2}
                            fill="url(#revWaveGrad)"
                          />
                          <Area
                            type="monotone"
                            dataKey="monthlyOpex"
                            name="Est. Total Costs (COGS+OpEx)"
                            stroke="#D97706"
                            strokeWidth={2}
                            fill="url(#costWaveGrad)"
                          />
                          <Line
                            type="monotone"
                            dataKey="monthlyNetProfit"
                            name="Est. Net Operating Profit"
                            stroke="#16A34A"
                            strokeWidth={2.5}
                            dot={{ r: 3.5, fill: '#16A34A', stroke: '#FFFFFF', strokeWidth: 1.5 }}
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    )}

                    {revenueView === 'donut' && (
                      <>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Tooltip
                              contentStyle={darkTooltipStyle}
                              formatter={(val) => Number(val || 0).toLocaleString()}
                            />
                            <Legend wrapperStyle={{ fontSize: '11px' }} />
                            <Pie
                              data={finData}
                              dataKey="monthlyNetProfit"
                              nameKey="shortName"
                              cx="50%"
                              cy="45%"
                              innerRadius={50}
                              outerRadius={80}
                              paddingAngle={5}
                              cornerRadius={8}
                            >
                              {finData.map((_, idx) => (
                                <Cell
                                  key={`prof-donut-${idx}`}
                                  fill={SAAS_PALETTE[(idx + 3) % SAAS_PALETTE.length]}
                                />
                              ))}
                            </Pie>
                          </PieChart>
                        </ResponsiveContainer>
                        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center -translate-y-3">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                            Avg Net Profit
                          </span>
                          <span className="text-xs font-extrabold text-emerald-400">
                            {finData.length > 0
                              ? Math.round(totalMonthlyProfit / finData.length).toLocaleString()
                              : '—'}
                          </span>
                        </div>
                      </>
                    )}

                    {revenueView === 'bar' && (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={finData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.16)" />
                          <XAxis dataKey="shortName" stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <YAxis stroke="#94A3B8" tick={{ fontSize: 10 }} />
                          <Tooltip contentStyle={darkTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px' }} />
                          <Bar
                            dataKey="monthlyRevenue"
                            name="Est. Monthly Revenue"
                            fill="#2563EB"
                            radius={[4, 4, 0, 0]}
                          />
                          <Bar
                            dataKey="monthlyOpex"
                            name="Est. Total Costs (COGS+OpEx)"
                            fill="#D97706"
                            radius={[4, 4, 0, 0]}
                          />
                          <Bar
                            dataKey="monthlyNetProfit"
                            name="Est. Net Operating Profit"
                            fill="#16A34A"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

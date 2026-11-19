import React, { useState } from 'react';
import {
  ArrowLeft,
  Download,
  Printer,
  Bookmark,
  GitCompare,
  MapPin,
  Wallet,
  TrendingUp,
  ShieldAlert,
  Award,
  CheckSquare,
  ExternalLink,
  Cpu,
  Radio,
  Users,
  Sparkles,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
} from 'recharts';
import ReportAssistantPanel from '../components/ReportAssistantPanel';
import { downloadOpportunityPdf } from '../services/api';

const chartTooltipStyle = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '8px',
  color: '#f8fafc',
  fontSize: '12px',
  boxShadow: '0 4px 12px rgba(15, 23, 42, 0.25)',
};

export default function ReportDetailPage({
  opportunity,
  onBack,
  onSaveReport,
  onToggleCompare,
  isCompared = false,
}) {
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [saveBanner, setSaveBanner] = useState('');

  if (!opportunity) return null;

  const sb = opportunity.startupBudget || {};
  const fp = opportunity.financialProjections || {};
  const sc = opportunity.scoreBreakdown || {};
  const nlp = opportunity.nlpInsights || {};
  const ap = opportunity.actionPlan || {};
  const ds = opportunity.dataSourceMetadata || {};
  const scenarios = fp.scenarios || [];
  const sixMonthData = fp.six_month_projection || [];
  const evidenceList = opportunity.evidenceSnippets || [];

  const handleDownloadPdf = async () => {
    setIsExportingPdf(true);
    try {
      await downloadOpportunityPdf(opportunity);
    } catch (e) {
      alert('PDF export failed: ' + e.message);
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleSave = async () => {
    if (!onSaveReport) return;
    await onSaveReport(opportunity);
    setSaveBanner('Report saved to your library');
    setTimeout(() => setSaveBanner(''), 3500);
  };

  return (
    <div className="space-y-6">
      {/* Top Action Bar (Hidden when printing) */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-3 no-print">
        <button
          type="button"
          onClick={onBack}
          className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-800 flex items-center gap-2 cursor-pointer transition"
        >
          <ArrowLeft className="w-4 h-4 text-blue-400" />
          <span>Back to Opportunities</span>
        </button>

        <div className="flex flex-wrap items-center gap-2">
          {saveBanner && (
            <span className="text-xs font-semibold text-emerald-400 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/25">
              {saveBanner}
            </span>
          )}

          <button
            type="button"
            onClick={handleSave}
            className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-800 flex items-center gap-1.5 cursor-pointer transition"
          >
            <Bookmark className="w-3.5 h-3.5 text-blue-400" />
            <span>Save Report</span>
          </button>

          {onToggleCompare && (
            <button
              type="button"
              onClick={() => onToggleCompare(opportunity)}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold border flex items-center gap-1.5 cursor-pointer transition ${
                isCompared
                  ? 'bg-blue-600/15 border-blue-500/40 text-blue-400'
                  : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300'
              }`}
            >
              <GitCompare className="w-3.5 h-3.5 text-blue-400" />
              <span>{isCompared ? 'In Comparison' : 'Compare'}</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => window.print()}
            className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-800 flex items-center gap-1.5 cursor-pointer transition"
          >
            <Printer className="w-3.5 h-3.5 text-slate-400" />
            <span>Print</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={isExportingPdf}
            className="btn-primary-text px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm cursor-pointer transition"
          >
            <Download className="w-3.5 h-3.5 text-white" />
            <span className="text-white">
              {isExportingPdf ? 'Generating PDF...' : 'Download PDF Report'}
            </span>
          </button>
        </div>
      </div>

      {/* Main Grid: Left 8 Cols Report Sections, Right 4 Cols Score & AI Assistant */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-8 space-y-6">
          {/* SECTION A: BUSINESS OVERVIEW */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-slate-800">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {opportunity.category}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-900 text-slate-300 border border-slate-800">
                    {opportunity.business_type}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                    {opportunity.confidenceLevel}
                  </span>
                </div>
                <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {opportunity.title}
                </h1>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <MapPin className="w-3.5 h-3.5 text-blue-400" />
                  <span>
                    {opportunity.area}, {opportunity.city}, {opportunity.state},{' '}
                    {opportunity.country} ({opportunity.country_code}) &bull; Currency:{' '}
                    {opportunity.currency} ({opportunity.currency_symbol})
                  </span>
                </div>
              </div>

              <div className="px-4 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-center shrink-0">
                <div className="text-2xl font-bold text-emerald-400 leading-none">
                  {opportunity.score}
                  <span className="text-xs font-normal opacity-80">/100</span>
                </div>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mt-1">
                  Viability Score
                </div>
              </div>
            </div>

            <p className="text-sm text-slate-200 leading-relaxed">{opportunity.summary}</p>

            {opportunity.crossRegionInsight?.is_cross_region_opportunity && (
              <div className="p-4 rounded-lg bg-amber-500/8 border border-amber-500/25 text-xs space-y-1.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-bold text-amber-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    Cross-State Proven Model: {opportunity.crossRegionInsight.badge_label} (
                    {opportunity.crossRegionInsight.proven_in_cities})
                  </div>
                  {opportunity.crossRegionInsight.recency_badge && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 text-[11px] font-medium">
                      {opportunity.crossRegionInsight.recency_badge}
                    </span>
                  )}
                </div>
                <p className="text-slate-300">
                  <strong className="text-white">
                    Origin Market ({opportunity.crossRegionInsight.proven_in_state}):
                  </strong>{' '}
                  {opportunity.crossRegionInsight.why_works_in_origin}
                </p>
                <p className="text-slate-300">
                  <strong className="text-blue-400">
                    Local Adaptation ({opportunity.city}, {opportunity.state}):
                  </strong>{' '}
                  {opportunity.crossRegionInsight.adaptation_tip}
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-xs font-semibold text-blue-400 mb-1">
                  Strategic Suitability
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {opportunity.whyThisOpportunity}
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-xs font-semibold text-emerald-400 mb-1 flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" />
                  Target Customer Segments
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {opportunity.targetCustomers}
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-xs font-semibold text-amber-400 mb-1">
                  Customer Problem Addressed
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {opportunity.customerProblem}
                </p>
              </div>
            </div>
          </div>

          {/* SECTION B: MARKET RESEARCH, NLP EVIDENCE & SOURCE LINKS */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                B. Market Research &amp; NLP Sentiment Findings
              </h2>
              <span className="text-xs px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1.5 font-medium">
                <Radio className="w-3.5 h-3.5" />
                {nlp.data_label || ds.data_status_label}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                <div className="font-semibold text-white">Estimated Demand &amp; Market Gap</div>
                <p className="text-slate-300">
                  <strong>Demand:</strong> {opportunity.estimatedDemand}
                </p>
                <p className="text-slate-300">
                  <strong>Market Gap:</strong> {opportunity.marketGap}
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                <div className="font-semibold text-white">
                  NLP Sentiment &amp; Problem-Theme Metrics
                </div>
                <p className="text-slate-300">
                  <strong>Engine:</strong> {nlp.model_name}
                </p>
                <p className="text-slate-300">
                  <strong>Records Analysed:</strong> {nlp.records_analysed} ({nlp.date_range}) &bull;{' '}
                  <strong>Sentiment:</strong> {nlp.overall_sentiment_label} (
                  {nlp.overall_sentiment_score})
                </p>
              </div>
            </div>

            {/* Observed Evidence vs AI Interpretation */}
            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs space-y-2">
              <div className="text-slate-200">{nlp.observed_evidence_summary}</div>
              <div className="text-slate-300 pt-1 border-t border-slate-800/80">
                {nlp.ai_interpretation_summary}
              </div>
            </div>

            {/* Recurring Complaints & Problem Themes */}
            {nlp.problem_themes && (
              <div>
                <div className="text-xs font-semibold text-slate-300 mb-2">
                  Clustered Problem Themes in {opportunity.city} ({opportunity.country})
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {nlp.problem_themes.slice(0, 3).map((th) => (
                    <div
                      key={th.theme}
                      className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs"
                    >
                      <div className="font-semibold text-white">{th.theme}</div>
                      <div className="text-blue-400 text-[11px] font-medium mt-0.5">
                        Relevance Score: {th.relevance_score}/100
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Keywords: {(th.matched_keywords || []).join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Clickable Evidence Snippets */}
            <div>
              <div className="text-xs font-semibold text-slate-300 mb-2">
                Analysed Market Evidence &amp; Source Citations ({evidenceList.length})
              </div>
              <div className="space-y-2.5">
                {evidenceList.slice(0, 5).map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="font-semibold text-white">{ev.title}</div>
                      <p className="text-slate-400 line-clamp-2">{ev.snippet}</p>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                        <span className="font-semibold text-blue-400">{ev.source_name}</span>
                        <span>&bull; Published: {ev.published_at}</span>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          VADER: {ev.sentiment_label} ({ev.sentiment_compound})
                        </span>
                      </div>
                    </div>
                    <a
                      href={ev.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 font-semibold flex items-center gap-1 shrink-0 self-start sm:self-center transition"
                    >
                      <span>Source</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION C: ITEMIZED STARTUP BUDGET BREAKDOWN */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Wallet className="w-4 h-4 text-emerald-500" />
                  C. Itemized Startup Budget Breakdown ({sb.currency})
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">{sb.cost_tier_note}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-emerald-400">{sb.total_formatted}</div>
                <div className="text-[11px] text-slate-400">
                  vs. Available Capital: {sb.user_budget_formatted} ({sb.budget_utilization_pct}%)
                </div>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-emerald-500/8 border border-emerald-500/25 text-xs text-emerald-300">
              <strong>Capital Fit Assessment:</strong> {sb.budget_comparison_note}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2.5 px-3 font-semibold">Expense Category</th>
                    <th className="py-2.5 px-3 font-semibold">Estimated Cost</th>
                    <th className="py-2.5 px-3 font-semibold">Share</th>
                    <th className="py-2.5 px-3 font-semibold">Requirement</th>
                    <th className="py-2.5 px-3 font-semibold">Verification Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70 text-slate-200">
                  {(sb.items || []).map((item, i) => (
                    <tr key={i}>
                      <td className="py-2.5 px-3 font-semibold text-white">{item.category}</td>
                      <td className="py-2.5 px-3 font-bold text-blue-400">{item.formatted}</td>
                      <td className="py-2.5 px-3">{item.share_pct}%</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            item.is_optional
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/25'
                              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                          }`}
                        >
                          {item.is_optional ? 'Optional / Deferrable' : 'Essential Core'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{item.verification_note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* SECTION D & E: REVENUE MODEL & FINANCIAL PROJECTIONS */}
          <div className="glass-panel p-6 space-y-5">
            <div className="pb-3 border-b border-slate-800">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-400" />
                D &amp; E. Revenue Model &amp; Financial Projections (Low / Base / High)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                <strong>Monetization Model:</strong> {opportunity.businessModel}
              </p>
            </div>

            {/* Key Projection Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400">Expected Monthly Revenue</div>
                <div className="text-sm font-bold text-white mt-1">
                  {fp.expected_monthly_revenue_range}
                </div>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400">Est. Monthly Gross Profit</div>
                <div className="text-sm font-bold text-blue-400 mt-1">
                  {fp.estimated_monthly_gross_profit}
                </div>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400">Est. Monthly Net Operating Profit</div>
                <div className="text-sm font-bold text-emerald-400 mt-1">
                  {fp.estimated_monthly_net_operating_profit}
                </div>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400">Est. Monthly Operating Expenses</div>
                <div className="text-xs font-semibold text-slate-200 mt-1">
                  {fp.estimated_monthly_operating_expenses}
                </div>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400">Break-Even Sales Estimate</div>
                <div className="text-xs font-semibold text-amber-400 mt-1">
                  {fp.break_even_estimate}
                </div>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400">Payback &amp; Net Margin</div>
                <div className="text-xs font-semibold text-indigo-400 mt-1">
                  {fp.approximate_payback_period} &bull; {fp.potential_profit_margin}
                </div>
              </div>
            </div>

            {/* Scenario Comparison Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2.5 px-3 font-semibold">Scenario</th>
                    <th className="py-2.5 px-3 font-semibold">Monthly Revenue</th>
                    <th className="py-2.5 px-3 font-semibold">Fixed OpEx</th>
                    <th className="py-2.5 px-3 font-semibold">Net Operating Profit</th>
                    <th className="py-2.5 px-3 font-semibold">Net Margin</th>
                    <th className="py-2.5 px-3 font-semibold">Est. Payback</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70 text-slate-200">
                  {scenarios.map((s) => (
                    <tr key={s.scenario_name}>
                      <td className="py-2.5 px-3 font-semibold text-white">{s.scenario_name}</td>
                      <td className="py-2.5 px-3">{s.monthly_revenue_formatted}</td>
                      <td className="py-2.5 px-3">{s.monthly_operating_expenses_formatted}</td>
                      <td className="py-2.5 px-3 font-bold text-emerald-400">
                        {s.monthly_net_profit_formatted}
                      </td>
                      <td className="py-2.5 px-3">{s.net_profit_margin_pct}%</td>
                      <td className="py-2.5 px-3 text-blue-400 font-medium">{s.payback_period_label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 6-Month Ramp-up Chart */}
            {sixMonthData.length > 0 && (
              <div className="h-60 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={sixMonthData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.35} />
                    <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={chartTooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      name="Est. Monthly Revenue"
                      stroke="#2563EB"
                      fill="#2563EB"
                      fillOpacity={0.14}
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="operating_costs"
                      name="Est. Total Costs (COGS + OpEx)"
                      stroke="#D97706"
                      fill="#D97706"
                      fillOpacity={0.1}
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="net_profit"
                      name="Est. Net Operating Profit"
                      stroke="#16A34A"
                      fill="#16A34A"
                      fillOpacity={0.18}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Assumptions, Formulas & Disclaimer */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="font-semibold text-slate-200">Documented Financial Formulas</div>
                {(fp.formulas_used || []).map((f, i) => (
                  <div key={i} className="text-slate-400">
                    &bull; {f}
                  </div>
                ))}
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="font-semibold text-slate-200">Operating Assumptions</div>
                {(fp.assumptions || []).map((a, i) => (
                  <div key={i} className="text-slate-400">
                    &bull; {a}
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-amber-500/8 border border-amber-500/25 text-[11px] text-amber-300">
              {fp.disclaimer}
            </div>
          </div>

          {/* SECTION F & G: COMPETITION, DIFFERENTIATION & RISK ASSESSMENT */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="glass-panel p-5 space-y-3">
              <h2 className="text-sm font-bold text-white">
                F. Competition &amp; Differentiation Strategy
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                {opportunity.competitorContext}
              </p>
              <div className="text-xs space-y-1">
                <div className="font-semibold text-emerald-400">Local Differentiation Levers:</div>
                {(opportunity.differentiationStrategies || []).map((d, idx) => (
                  <div key={idx} className="text-slate-300">
                    &bull; {d}
                  </div>
                ))}
              </div>
              <div className="text-xs text-slate-300 pt-2 border-t border-slate-800">
                <strong>Pricing &amp; Service Strategy:</strong>{' '}
                {opportunity.pricingAndServiceStrategy}
              </div>
            </div>

            <div className="glass-panel p-5 space-y-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                G. Risk Assessment &amp; Mitigation
              </h2>
              <div className="space-y-2.5">
                {(opportunity.riskAssessment || []).map((r, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center justify-between font-semibold text-white">
                      <span>{r.category}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/25">
                        {r.severity} Risk
                      </span>
                    </div>
                    <p className="text-slate-400 mt-1">{r.description}</p>
                    <p className="text-emerald-400 mt-1">
                      <strong>Mitigation:</strong> {r.mitigation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION I: 30-DAY ACTION PLAN & VALIDATION CHECKLIST */}
          <div className="glass-panel p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-emerald-500" />
              I. Action Plan, Equipment, Suppliers &amp; First 30 Days
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                <div className="font-semibold text-blue-400">Core Equipment &amp; Resources</div>
                {(ap.basic_equipment_and_resources || []).map((eq, i) => (
                  <div key={i} className="text-slate-300">
                    &bull; {eq}
                  </div>
                ))}
              </div>
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                <div className="font-semibold text-emerald-400">
                  Suppliers, Sourcing &amp; Licensing
                </div>
                {(ap.potential_suppliers_or_sourcing || []).map((sp, i) => (
                  <div key={i} className="text-slate-300">
                    &bull; <strong>Supplier:</strong> {sp}
                  </div>
                ))}
                {(ap.licences_to_investigate || []).map((lc, i) => (
                  <div key={i} className="text-amber-400">
                    &bull; <strong>Licence:</strong> {lc}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
              {(ap.first_30_day_plan || []).map((w, i) => (
                <div key={i} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <div className="font-semibold text-blue-400">{w.week}</div>
                  <p className="text-slate-300 mt-1 leading-relaxed">{w.focus}</p>
                </div>
              ))}
            </div>

            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white">
                Pre-Investment Field Validation Checklist:
              </div>
              {(ap.validation_questions || []).map((vq, i) => (
                <div key={i} className="text-slate-300">
                  {i + 1}. {vq}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 4 Columns: SECTION H (Transparent Score Breakdown) + AI Report Assistant */}
        <div className="xl:col-span-4 space-y-6">
          {/* SECTION H: TRANSPARENT 5-FACTOR OPPORTUNITY SCORE */}
          <div className="glass-panel p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-emerald-500" />
                  H. Viability Score Breakdown
                </h2>
                <p className="text-[11px] text-slate-400">
                  5-factor weighted model
                </p>
              </div>
              <span className="text-lg font-bold text-emerald-400">
                {opportunity.score}/100
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-blue-400">
              {sc.formula}
            </div>

            <div className="space-y-3">
              {(sc.factors || []).map((f) => (
                <div
                  key={f.key}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs"
                >
                  <div className="flex items-center justify-between font-semibold text-white mb-1.5">
                    <span>
                      {f.name} ({f.weight_pct}%)
                    </span>
                    <span className="text-blue-400">
                      {f.score}/100 &rarr; +{f.weighted_points} pts
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden mb-1.5">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{ width: `${f.score}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">{f.explanation}</p>
                </div>
              ))}
            </div>

            <p className="text-[11px] text-slate-400 italic">{sc.methodology_note}</p>
          </div>

          {/* Interactive Report Assistant Panel */}
          <ReportAssistantPanel opportunity={opportunity} />

          {/* Data Source Metadata Card */}
          <div className="glass-panel p-5 space-y-2 text-xs">
            <div className="font-semibold text-white flex items-center gap-1.5">
              <Info className="w-4 h-4 text-blue-400" />
              Data Sources &amp; Coverage Metadata
            </div>
            <div className="text-slate-300">
              <strong>Source:</strong> {ds.market_data_source}
            </div>
            <div className="text-slate-300">
              <strong>Status:</strong> {ds.data_status_label}
            </div>
            <div className="text-slate-300">
              <strong>Coverage:</strong> {ds.geographical_coverage}
            </div>
            <div className="text-slate-400 text-[11px] leading-relaxed">{ds.coverage_note}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

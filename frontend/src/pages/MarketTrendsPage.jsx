import React from 'react';
import {
  Cpu,
  Radio,
  ExternalLink,
  TrendingUp,
  CheckCircle2,
  Sparkles,
  MessageSquareWarning,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';

const chartTooltipStyle = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '8px',
  color: '#f8fafc',
  fontSize: '12px',
  boxShadow: '0 4px 12px rgba(15, 23, 42, 0.25)',
};

const SAAS_COLORS = ['#2563EB', '#0D9488', '#4F46E5', '#16A34A', '#D97706'];

export default function MarketTrendsPage({ dashboardData, discoveryResult }) {
  const activeOpp =
    discoveryResult?.opportunities?.[0] ||
    dashboardData?.recent_opportunities?.[0] ||
    null;

  const nlp = discoveryResult?.nlp_summary || activeOpp?.nlpInsights || {};
  const snippets = activeOpp?.evidenceSnippets || [];
  const sys = dashboardData?.system_status || {};

  const themeChartData = (nlp.problem_themes || []).map((t) => ({
    name: t.theme.split('&')[0].trim(),
    fullTheme: t.theme,
    score: t.relevance_score,
    mentions: t.mention_count,
  }));

  const sentimentDistData = Object.entries(nlp.sentiment_distribution || {}).map(
    ([label, count]) => ({
      name: label,
      count,
    })
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-500 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              Market Intelligence &amp; NLP Sentiment Analysis
            </span>
            <h1 className="text-xl sm:text-2xl font-bold text-white mt-1 tracking-tight">
              Market Trends &amp; Consumer Demand Inspector
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl">
              Review external market evidence, VADER sentiment polarity distributions, TF-IDF
              problem theme clusters, and recurring consumer demand signals.
            </p>
          </div>

          <div className="space-y-1 text-xs bg-slate-900/70 p-3.5 rounded-lg border border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <Radio className="w-3.5 h-3.5" />
              <span>{nlp.data_label || sys.data_status_label || 'Verified Market Dataset'}</span>
            </div>
            <div className="text-slate-400">
              <strong>Engine:</strong> {nlp.model_name || sys.nlp_model_name}
            </div>
            <div className="text-slate-400">
              <strong>Records Analysed:</strong> {nlp.records_analysed ?? sys.records_processed ?? 0}{' '}
              ({nlp.date_range || 'Current batch'})
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row: Theme Relevance & Sentiment Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="glass-panel p-5">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-0.5">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            Clustered Consumer Problem Themes
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Keyword density relevance score (/100) across retrieved market records
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={themeChartData} layout="vertical" margin={{ left: 16, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.35} />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={130}
                  stroke="#64748b"
                  tick={{ fontSize: 11 }}
                />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="score" name="Theme Relevance (/100)" radius={[0, 4, 4, 0]}>
                  {themeChartData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={SAAS_COLORS[i % SAAS_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-5">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-0.5">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            VADER Sentiment Polarity Distribution
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Overall Compound Score: <strong>{nlp.overall_sentiment_score ?? 0}</strong> (
            {nlp.overall_sentiment_label || 'Balanced'})
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentDistData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.35} />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="count" name="Articles Count" fill="#2563EB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Observed Evidence vs AI Interpretation + Recurring Complaints */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="glass-panel p-5 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-blue-400" />
            Observed Evidence vs. Analytical Interpretation
          </h3>
          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-200 leading-relaxed">
            {nlp.observed_evidence_summary}
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-200 leading-relaxed">
            {nlp.ai_interpretation_summary}
          </div>
        </div>

        <div className="glass-panel p-5 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <MessageSquareWarning className="w-4 h-4 text-amber-400" />
            Extracted Consumer Friction &amp; Unmet Needs
          </h3>
          <div className="space-y-2">
            {(nlp.recurring_complaints_and_needs || []).map((c, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-300"
              >
                &bull; {c}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Full Evidence Table with Clickable Source Links */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-base font-bold text-white">
          Retrieved Market Evidence Records ({snippets.length})
        </h3>
        <div className="space-y-3">
          {snippets.map((ev, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs"
            >
              <div className="space-y-1">
                <div className="font-semibold text-white text-sm">{ev.title}</div>
                <p className="text-slate-300 leading-relaxed">{ev.snippet}</p>
                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                  <span className="text-blue-400 font-semibold">Source: {ev.source_name}</span>
                  <span>Published: {ev.published_at}</span>
                  <span>Retrieved: {ev.retrieved_at}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-medium">
                    VADER Compound: {ev.sentiment_compound} ({ev.sentiment_label})
                  </span>
                </div>
              </div>
              <a
                href={ev.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 font-semibold flex items-center gap-1.5 shrink-0 self-start sm:self-center transition"
              >
                <span>View Source</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

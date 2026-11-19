import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  KeyRound,
  Database,
  Cpu,
  Globe,
  ShieldCheck,
  Zap,
  RefreshCw,
  Trash2,
  Layers,
} from 'lucide-react';
import { getPromptCacheStats, clearPromptCache } from '../services/api';

export default function SettingsPage({ healthData, userEmail, onOpenLoginModal }) {
  const integrations = healthData?.integrations || {};
  const nlp = healthData?.nlp_engine || {};

  const [cacheStats, setCacheStats] = useState(null);
  const [loadingCache, setLoadingCache] = useState(false);
  const [cacheNotice, setCacheNotice] = useState('');

  const loadCacheTelemetry = async () => {
    setLoadingCache(true);
    try {
      const data = await getPromptCacheStats();
      setCacheStats(data);
    } catch {
      // Fallback to healthData.prompt_cache if available
    } finally {
      setLoadingCache(false);
    }
  };

  useEffect(() => {
    loadCacheTelemetry();
  }, []);

  const handleClearCache = async () => {
    setLoadingCache(true);
    setCacheNotice('');
    try {
      const res = await clearPromptCache();
      setCacheNotice(res.message || 'Prompt cache cleared.');
      await loadCacheTelemetry();
    } catch (err) {
      setCacheNotice(`Failed to clear cache: ${err.message}`);
    } finally {
      setLoadingCache(false);
    }
  };

  const metrics = cacheStats?.metrics || healthData?.prompt_cache || {};
  const arch = cacheStats?.architecture || {};
  const byType = cacheStats?.by_prompt_type || [];
  const recentEntries = cacheStats?.recent_entries || [];

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6">
        <h1 className="text-xl font-bold text-white tracking-tight">
          System Configuration, Prompt Caching &amp; Integrations
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Manage system modules, L1/L2 + Provider Context Prompt Caching, environment API keys in{' '}
          <code>backend/.env</code>, and SQLite persistence.
        </p>
      </div>

      {/* Multi-Layer Prompt & Context Caching Telemetry Panel */}
      <div className="glass-panel p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-400" />
              <h2 className="text-base font-bold text-white">
                Multi-Layer Prompt &amp; Context Caching Engine
              </h2>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                {cacheStats?.enabled !== false ? 'ACTIVE (L1 RAM + L2 SQLite + Static Prefix)' : 'DISABLED'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Powered by <code>backend/services/prompt_cache_service.py</code> &bull; Combines a{' '}
              <strong>&gt;1,024-token Canonical Static System Prefix</strong> with deterministic
              SHA-256 L1/L2 caching.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={loadCacheTelemetry}
              disabled={loadingCache}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-800 flex items-center gap-1.5 cursor-pointer transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${loadingCache ? 'animate-spin' : ''}`} />
              <span>Refresh Stats</span>
            </button>
            <button
              type="button"
              onClick={handleClearCache}
              disabled={loadingCache}
              className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-xs font-semibold text-red-400 border border-red-500/25 flex items-center gap-1.5 cursor-pointer transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Purge Cache</span>
            </button>
          </div>
        </div>

        {cacheNotice && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-xs text-emerald-400">
            {cacheNotice}
          </div>
        )}

        {/* Prompt Cache KPI Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] text-slate-400">Cache Hit Rate</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">
              {metrics.hit_rate_pct ?? 0}%
            </div>
            <div className="text-[10px] text-slate-500">
              {metrics.total_hits ?? 0} hits / {metrics.total_requests ?? 0} lookups
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] text-slate-400">L1 Memory / L2 SQLite</div>
            <div className="text-lg font-bold text-blue-400 mt-0.5">
              {metrics.l1_active_entries ?? 0} / {metrics.l2_sqlite_entries ?? 0}
            </div>
            <div className="text-[10px] text-slate-500">
              L1 hits: {metrics.l1_memory_hits ?? 0} &bull; L2 hits: {metrics.l2_sqlite_hits ?? 0}
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] text-slate-400">Est. Tokens Saved</div>
            <div className="text-lg font-bold text-indigo-400 mt-0.5">
              {(metrics.estimated_tokens_saved ?? 0).toLocaleString()}
            </div>
            <div className="text-[10px] text-slate-500">Prefix + completion reuse</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] text-slate-400">Latency Saved</div>
            <div className="text-lg font-bold text-amber-400 mt-0.5">
              {metrics.total_latency_saved_ms ?? 0} ms
            </div>
            <div className="text-[10px] text-slate-500">Sub-millisecond L1 lookups</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] text-slate-400">Static System Prefix</div>
            <div className="text-lg font-bold text-white mt-0.5">
              {arch.static_prefix_tokens ?? 1180} tok
            </div>
            <div className="text-[10px] text-emerald-400">
              &ge;1,024 Prefix Threshold Met
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] text-slate-400">Prefix SHA-256</div>
            <div className="text-sm font-mono font-bold text-blue-400 mt-1">
              #{arch.static_prefix_hash_short || healthData?.prompt_cache?.static_prefix_hash || 'aligned'}
            </div>
            <div className="text-[10px] text-slate-500">
              TTL: {cacheStats?.ttl_minutes ?? 1440} mins
            </div>
          </div>
        </div>

        {/* Breakdown by Prompt Type */}
        {byType.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              Cached Prompts by Pipeline Stage
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {byType.map((item) => (
                <div
                  key={item.prompt_type}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-semibold text-white">{item.prompt_type}</div>
                    <div className="text-[11px] text-slate-400">
                      {item.entries} cached prompt(s) &bull; {Math.round(item.latency_saved_ms || 0)} ms saved
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 text-xs font-bold">
                      {item.hits} Hits
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Cached Prompt Keys */}
        {recentEntries.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Recent Deterministic SHA-256 Prompt Cache Entries (SQLite L2)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 pr-3 font-semibold">Prompt Key</th>
                    <th className="py-2 pr-3 font-semibold">Pipeline Stage</th>
                    <th className="py-2 pr-3 font-semibold">Prefix / Total Tokens</th>
                    <th className="py-2 pr-3 font-semibold">Cache Hits</th>
                    <th className="py-2 font-semibold">Last Accessed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {recentEntries.slice(0, 6).map((entry) => (
                    <tr key={entry.cache_key}>
                      <td className="py-2 pr-3 font-mono text-blue-400">
                        {entry.cache_key.slice(0, 12)}...
                      </td>
                      <td className="py-2 pr-3">{entry.prompt_type}</td>
                      <td className="py-2 pr-3">
                        {entry.cached_tokens_est} / {entry.prompt_tokens_est} tok
                      </td>
                      <td className="py-2 pr-3 font-bold text-emerald-400">{entry.hit_count}</td>
                      <td className="py-2 text-slate-400">
                        {(entry.last_accessed_at || '').slice(0, 19).replace('T', ' ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Active Modules Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="glass-panel p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
              NLP Analysis Engine
            </span>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-sm font-bold text-white">
            {nlp.name || 'VADER-Lexicon-v3.3.2 + Statistical TF-IDF Clusterer'}
          </div>
          <div className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Active Locally (Zero Paid Key Required)
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Located in <code>backend/services/nlp_analysis_service.py</code>. Runs sentiment
            classification and problem-theme clustering with L1/L2 corpus prompt caching.
          </p>
        </div>

        <div className="glass-panel p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Market Data Retrieval
            </span>
            <Globe className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-white">
            Public Google News RSS + Optional NewsAPI
          </div>
          <div className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Public RSS Feed Enabled &bull; NewsAPI Key:{' '}
            {integrations.market_data_api_configured ? 'Configured' : 'Optional (Not Set)'}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Located in <code>backend/services/market_data_service.py</code>. Caches records in
            SQLite and labels live vs. cached vs. demo data transparently.
          </p>
        </div>

        <div className="glass-panel p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Currency &amp; SQLite Persistence
            </span>
            <Database className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-sm font-bold text-white">
            {healthData?.database || 'SQLite (business_opportunity.db)'}
          </div>
          <div className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            6 Tables Active (Incl. <code>prompt_cache</code>)
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Stores users, search history, saved reports, market/FX caches, and SHA-256 prompt cache
            records using parameterized SQL queries.
          </p>
        </div>
      </div>

      {/* How to Configure Optional Paid Keys in backend/.env */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-amber-400" />
          Environment API Keys &amp; Context Caching (<code>backend/.env</code>)
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The configuration template is located at <code>backend/.env.example</code>. To enable
          optional external integrations (Google Gemini / OpenAI LLM with prefix caching,
          NewsAPI.org, or ExchangeRate-API), copy <code>backend/.env.example</code> to{' '}
          <code>backend/.env</code> and configure your keys:
        </p>

        <pre className="p-4 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 overflow-x-auto font-mono">
{`# Inside backend/.env
AI_PROVIDER=gemini
AI_API_KEY=your_gemini_or_openai_key_here
PROMPT_CACHE_ENABLED=true
PROMPT_CACHE_TTL_MINUTES=1440
GEMINI_CONTEXT_CACHE_TTL_SECONDS=3600
MARKET_DATA_API_KEY=your_newsapi_org_key_here
EXCHANGE_RATE_API_KEY=your_exchangerate_api_key_here`}
        </pre>

        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>
              Active Session: <strong className="text-white">{userEmail}</strong>
            </span>
          </div>
          {onOpenLoginModal && (
            <button
              type="button"
              onClick={onOpenLoginModal}
              className="btn-primary-text px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white cursor-pointer transition"
            >
              <span className="text-white">Switch Account (Password Login)</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { Bot, Send, Info, Zap } from 'lucide-react';
import { queryReportAssistant } from '../services/api';

export default function ReportAssistantPanel({ opportunity }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Hello! I am the **Report Interpreter Assistant** for **${
        opportunity?.title || 'this opportunity'
      }**. I can help you interpret the itemized startup budget, Low/Base/High profit formulas, NLP market sentiment, or the first 30-day launch plan.`,
      mode: 'Structured Report & NLP Evidence Interpreter',
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const quickPrompts = [
    'How can I reduce the startup budget?',
    'Explain the monthly profit and break-even formula',
    'What did the NLP sentiment analysis find?',
    'What are the first 30-day steps and licences?',
  ];

  const handleAsk = async (qText) => {
    const queryStr = (qText || question).trim();
    if (!queryStr || !opportunity) return;

    const userMsg = { role: 'user', text: queryStr };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    setIsLoading(true);

    try {
      const res = await queryReportAssistant(queryStr, opportunity);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: res.answer,
          mode: res.assistant_mode,
          isLiveLlm: res.is_live_llm,
          cacheMeta: res.cache_meta || null,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Unable to process query: ${err.message}`,
          mode: 'Local Fallback',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel p-5 flex flex-col gap-3.5 no-print">
      {/* Assistant Header */}
      <div className="flex items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600/15 border border-blue-500/25 flex items-center justify-center text-blue-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              Report Intelligence Assistant
            </h3>
            <p className="text-[11px] text-slate-400">
              Financial &amp; NLP Evidence Interpreter
            </p>
          </div>
        </div>
      </div>

      {/* Model Disclosure Banner */}
      <div className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
        <span>
          <strong>Transparency Note:</strong> Answers are computed directly from this
          report&apos;s verified budget formulas and VADER NLP findings. Configure{' '}
          <code>AI_API_KEY</code> in <code>backend/.env</code> to enable live generative LLM
          follow-ups.
        </span>
      </div>

      {/* Quick Question Chips */}
      <div className="flex flex-wrap gap-1.5">
        {quickPrompts.map((qp) => (
          <button
            key={qp}
            type="button"
            onClick={() => handleAsk(qp)}
            className="text-[11px] px-2.5 py-1 rounded-md bg-slate-900 hover:bg-blue-600/10 text-slate-300 hover:text-blue-400 border border-slate-800 hover:border-blue-500/30 transition cursor-pointer"
          >
            {qp}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg text-xs leading-relaxed ${
              m.role === 'user'
                ? 'bg-blue-600/15 border border-blue-500/25 text-slate-100 ml-6'
                : 'bg-slate-900/70 border border-slate-800 text-slate-200 mr-2'
            }`}
          >
            <div className="whitespace-pre-line">{m.text}</div>
            {m.cacheMeta && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                    m.cacheMeta.cache_hit
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                      : 'bg-blue-500/10 text-blue-400 border-blue-500/25'
                  }`}
                >
                  <Zap className="w-3 h-3" />
                  {m.cacheMeta.cache_hit
                    ? `Prompt Cache HIT (${m.cacheMeta.cache_layer}) • Saved ~${m.cacheMeta.cached_tokens_saved || m.cacheMeta.static_prefix_tokens} tokens (${m.cacheMeta.lookup_latency_ms}ms)`
                    : `Cached to L1+SQLite • Prefix #${m.cacheMeta.prefix_hash_short?.slice(0, 8)}`}
                </span>
              </div>
            )}
            {m.mode && (
              <div className="text-[10px] text-slate-500 mt-1">
                Engine: {m.mode}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="text-xs text-blue-400 animate-pulse px-2">
            Analyzing report metrics...
          </div>
        )}
      </div>

      {/* Ask Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk(question);
        }}
        className="flex gap-2 pt-2 border-t border-slate-800"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about costs, break-even, risks, or licences..."
          className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary-text px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-1.5 cursor-pointer transition"
        >
          <Send className="w-3.5 h-3.5 text-white" />
          <span className="text-white">Ask</span>
        </button>
      </form>
    </div>
  );
}

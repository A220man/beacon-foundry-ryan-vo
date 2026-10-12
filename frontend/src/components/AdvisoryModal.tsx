import React, { useState } from 'react';
import { AdvisoryResponse } from '../api/client';

interface Props {
  advisory: AdvisoryResponse | null;
  loading: boolean;
  onRequestAdvisory: (query: string) => void;
}

export const AdvisoryModal: React.FC<Props> = ({ advisory, loading, onRequestAdvisory }) => {
  const [query, setQuery] = useState(
    'Analyze the AGC assembly opcode context and provide historical flight mission implications.'
  );

  return (
    <div className="card p-6 space-y-4">
      <div className="border-b border-slate-700/60 pb-3">
        <h3 className="text-xl font-semibold text-white">Advisory Guidance Assistant</h3>
        <p className="text-xs text-slate-400">
          Operator-configured LLM analysis (OpenAI, Anthropic, Gemini, Ollama) grounded in Apollo records
        </p>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Analysis Prompt / Query:
          </label>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            rows={2}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <button
          onClick={() => onRequestAdvisory(query)}
          disabled={loading}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold rounded border border-slate-700 transition"
        >
          {loading ? 'Consulting Grounded Engine...' : 'Run Advisory Explanation'}
        </button>
      </div>

      {advisory && (
        <div className="mt-4 bg-slate-900/80 border border-slate-700/60 rounded p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span>Provider: <strong className="text-slate-200">{advisory.provider}</strong></span>
            <span>Model: <strong className="text-slate-200">{advisory.model}</strong></span>
            <span className="text-cyan-400 font-mono text-[11px]">{advisory.confidence_assessment}</span>
          </div>
          <div className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
            {advisory.advisory_text}
          </div>
        </div>
      )}
    </div>
  );
};

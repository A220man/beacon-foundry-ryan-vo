import React from 'react';
import { MLEvalResult } from '../api/client';

interface Props {
  result: MLEvalResult | null;
  loading: boolean;
  onRunBenchmark: () => void;
}

export const BenchmarkDashboard: React.FC<Props> = ({ result, loading, onRunBenchmark }) => (
  <div className="card p-6 space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
      <div>
        <h3 className="text-xl font-semibold text-white">AI/ML Alignment Evaluation Suite</h3>
        <p className="text-xs text-slate-400">Lexical Heuristics vs 64-dim Fourier Token Cosine Embeddings</p>
      </div>
      <button onClick={onRunBenchmark} disabled={loading} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold shadow transition disabled:opacity-50">
        {loading ? 'Running Benchmark...' : 'Run Evaluation Suite'}
      </button>
    </div>

    {!result ? (
      <div className="text-center py-8 text-slate-400 text-sm">Click above to trigger the reproducible evaluation suite against the 40-sample Apollo 11 historical corpus.</div>
    ) : (
      <div className="space-y-6">
        <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 text-xs text-slate-300">
          <span className="font-semibold text-cyan-400">Executive Summary: </span>{result.summary}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
            <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2"><span className="w-5 h-5 rounded bg-slate-700 flex items-center justify-center text-slate-300 text-xs">H</span>Heuristic Baseline (Token Jaccard / Levenshtein)</h4>
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-slate-300">{result.baseline_metrics.precision.toFixed(2)}</div><div className="text-xs text-slate-400">Precision</div></div>
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-slate-300">{result.baseline_metrics.recall.toFixed(2)}</div><div className="text-xs text-slate-400">Recall</div></div>
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-cyan-400">{result.baseline_metrics.f1_score.toFixed(2)}</div><div className="text-xs text-slate-400">F1-Score</div></div>
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-slate-300">{result.baseline_metrics.roc_auc.toFixed(2)}</div><div className="text-xs text-slate-400">ROC-AUC</div></div>
              <div className="bg-slate-800 rounded p-3 col-span-2"><div className="text-xl font-bold text-slate-300">{result.baseline_metrics.mean_latency_ms.toFixed(1)}ms</div><div className="text-xs text-slate-400">Mean Latency</div></div>
            </div>
          </div>

          <div className="bg-slate-900 border border-cyan-800/40 rounded-lg p-5 space-y-4 shadow-sm shadow-cyan-950">
            <h4 className="text-sm font-semibold text-cyan-300 flex items-center gap-2"><span className="w-5 h-5 rounded bg-cyan-900/50 flex items-center justify-center text-cyan-300 text-xs">E</span>Embedding Cosine Model (64-dim Fourier Token Projection)</h4>
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-cyan-300">{result.embedding_metrics.precision.toFixed(2)}</div><div className="text-xs text-slate-400">Precision</div></div>
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-cyan-300">{result.embedding_metrics.recall.toFixed(2)}</div><div className="text-xs text-slate-400">Recall</div></div>
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-emerald-400">{result.embedding_metrics.f1_score.toFixed(2)}</div><div className="text-xs text-slate-400">F1-Score</div></div>
              <div className="bg-slate-800 rounded p-3"><div className="text-2xl font-bold text-cyan-300">{result.embedding_metrics.roc_auc.toFixed(2)}</div><div className="text-xs text-slate-400">ROC-AUC</div></div>
              <div className="bg-slate-800 rounded p-3 col-span-2"><div className="text-xl font-bold text-cyan-300">{result.embedding_metrics.mean_latency_ms.toFixed(1)}ms</div><div className="text-xs text-slate-400">Mean Latency</div></div>
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-400 bg-slate-950 p-3 rounded border border-slate-800">
          <span className="font-semibold">Data Provenance:</span> 40 curated Apollo 11 Luminary 099 snippets (WAITLIST, POWERED_FLIGHT, PHASE_TABLE, ORBITAL_INTEGRATION, TIME_OF_FREE_FALL, TJET_LAW). 20 clean / 20 corrupted with OCR noise, dropped banks, transposed opcodes. Ground truth from ibiblio.org scan cross-references.
        </div>
      </div>
    )}
  </div>
);
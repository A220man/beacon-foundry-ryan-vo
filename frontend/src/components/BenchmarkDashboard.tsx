import React from 'react';
import { MLEvalResult } from '../api/client';

interface Props {
  result: MLEvalResult | null;
  loading: boolean;
  onRunBenchmark: () => void;
}

export const BenchmarkDashboard: React.FC<Props> = ({ result, loading, onRunBenchmark }) => {
  return (
    <div className="card p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
        <div>
          <h3 className="text-xl font-semibold text-white">AI/ML Alignment Evaluation Suite</h3>
          <p className="text-xs text-slate-400">
            Comparative benchmark: Lexical Heuristics vs 64-dim Fourier Token Cosine Embeddings
          </p>
        </div>
        <div>
          <button
            onClick={onRunBenchmark}
            disabled={loading}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow transition"
          >
            {loading ? 'Evaluating Model Inferences...' : 'Run Benchmark Evaluation'}
          </button>
        </div>
      </div>

      {!result ? (
        <div className="text-center py-8 text-slate-400 text-sm">
          Click above to trigger the reproducible evaluation suite against the 40-sample Apollo 11 historical corpus.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 text-xs text-slate-300">
            <span className="font-semibold text-cyan-400">Executive Summary: </span>
            {result.summary}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Baseline Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="font-semibold text-slate-200 text-sm">Baseline: Heuristic Token Rule Model</h4>
                <span className="text-xs text-slate-400 font-mono">Lexical Lookup</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">Precision</div>
                  <div className="text-lg font-mono font-bold text-white">
                    {(result.baseline_metrics.precision * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">Recall</div>
                  <div className="text-lg font-mono font-bold text-white">
                    {(result.baseline_metrics.recall * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">F1 Score</div>
                  <div className="text-lg font-mono font-bold text-cyan-400">
                    {result.baseline_metrics.f1_score.toFixed(3)}
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">ROC AUC</div>
                  <div className="text-lg font-mono font-bold text-cyan-400">
                    {result.baseline_metrics.roc_auc.toFixed(3)}
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-400 flex justify-between font-mono pt-1">
                <span>Mean Inference Latency:</span>
                <span>{result.baseline_metrics.mean_latency_ms} ms / sample</span>
              </div>
            </div>

            {/* Embedding Model Card */}
            <div className="bg-slate-900 border border-cyan-800/40 rounded-lg p-5 space-y-4 shadow-sm shadow-cyan-950">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="font-semibold text-cyan-300 text-sm">Fourier Embedding Cosine Detector</h4>
                <span className="text-xs bg-cyan-950 text-cyan-400 px-2 py-0.5 rounded font-mono border border-cyan-800">
                  64-dim Projection
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">Precision</div>
                  <div className="text-lg font-mono font-bold text-emerald-400">
                    {(result.embedding_metrics.precision * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">Recall</div>
                  <div className="text-lg font-mono font-bold text-emerald-400">
                    {(result.embedding_metrics.recall * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">F1 Score</div>
                  <div className="text-lg font-mono font-bold text-emerald-400">
                    {result.embedding_metrics.f1_score.toFixed(3)}
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500">ROC AUC</div>
                  <div className="text-lg font-mono font-bold text-emerald-400">
                    {result.embedding_metrics.roc_auc.toFixed(3)}
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-400 flex justify-between font-mono pt-1">
                <span>Mean Inference Latency:</span>
                <span>{result.embedding_metrics.mean_latency_ms} ms / sample</span>
              </div>
            </div>
          </div>

          <div className="text-xs text-slate-400 bg-slate-950 p-3 rounded border border-slate-800">
            <strong>Evaluation Details:</strong> Tested against {result.total_samples} labeled historical snippets across 
            Apollo 11 subroutines (WAITLIST, POWERED_FLIGHT, PHASE_TABLE_MAINTENANCE). Timestamp: {result.timestamp}
          </div>
        </div>
      )}
    </div>
  );
};

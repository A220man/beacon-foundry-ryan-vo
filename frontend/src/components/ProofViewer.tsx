import React from 'react';
import { ProofResult } from '../api/client';

interface Props {
  result: ProofResult | null;
  onAdvisoryRequest?: (discrepancy: any) => void;
}

export const ProofViewer: React.FC<Props> = ({ result, onAdvisoryRequest }) => {
  if (!result) {
    return (
      <div className="card p-6 text-center text-slate-400">
        No proofing results available. Submit Apollo Guidance Computer assembly to compare against baseline scans.
      </div>
    );
  }

  return (
    <div className="card p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
        <div>
          <h3 className="text-xl font-semibold text-white">AGC Microfilm Proofing Report</h3>
          <p className="text-xs text-slate-400">
            AST verification and syntax anomaly detection against historical Apollo 11 listings
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
            result.status === 'PASSED'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
          }`}>
            {result.status}
          </span>
          <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
            Quality: {(result.quality_score * 100).toFixed(1)}%
          </span>
          <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
            Parsed: {result.parsed_instructions} ops / {result.total_lines} lines
          </span>
        </div>
      </div>

      {result.discrepancies.length === 0 ? (
        <div className="bg-emerald-950/20 border border-emerald-800/40 p-4 rounded text-sm text-emerald-300">
          ✓ All instructions match recognized Apollo guidance opcodes, memory operands, and bank assignments.
        </div>
      ) : (
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-slate-200">
            Detected Discrepancies ({result.discrepancies.length})
          </h4>
          <div className="space-y-3">
            {result.discrepancies.map((disc, idx) => (
              <div
                key={idx}
                className="bg-slate-900 border border-amber-800/30 rounded p-4 space-y-2 hover:border-amber-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-amber-900/40 text-amber-400 text-xs font-mono rounded">
                      Line {disc.line_number}
                    </span>
                    <span className="text-xs font-semibold text-slate-300 uppercase">
                      {disc.issue_type}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    Confidence: {(disc.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono pt-1">
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block mb-1">Scanned / Expected:</span>
                    <span className="text-emerald-400">{disc.scanned_text}</span>
                  </div>
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block mb-1">Transcribed Input:</span>
                    <span className="text-rose-400">{disc.transcribed_text}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-400 italic">
                  💡 {disc.suggestion}
                </p>

                {onAdvisoryRequest && (
                  <div className="pt-1 flex justify-end">
                    <button
                      onClick={() => onAdvisoryRequest(disc)}
                      className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 transition"
                    >
                      Request LLM Advisory Analysis →
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

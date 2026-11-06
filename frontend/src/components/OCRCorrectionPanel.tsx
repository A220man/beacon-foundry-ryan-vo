import React, { useState } from 'react';
import { api, OCRCorrectionResult, OCRCorrectionSummary } from '../api/client';

interface OCRCorrectionPanelProps {
  programId: string;
  transcriptionText: string;
  onApplyCorrections: (correctedText: string) => void;
}

export const OCRCorrectionPanel: React.FC<OCRCorrectionPanelProps> = ({
  programId,
  transcriptionText,
  onApplyCorrections
}) => {
  const [result, setResult] = useState<OCRCorrectionResult | null>(null);
  const [summary, setSummary] = useState<OCRCorrectionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!transcriptionText.trim()) {
      setError('No transcription text to analyze');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.ocrCorrectTranscription(programId, transcriptionText);
      setResult(res);
      const sum = await api.getOcrCorrectionSummary(programId);
      setSummary(sum);
    } catch (err: any) {
      setError(err.message || 'OCR analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    if (result) {
      onApplyCorrections(result.corrected_text);
    }
  };

  const handleProofWithOcr = async () => {
    if (!transcriptionText.trim()) {
      setError('No transcription text to proof');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.proofWithOcrPreprocessing(transcriptionText);
      // This would typically be handled by the parent component
      console.log('Proof with OCR result:', res);
    } catch (err: any) {
      setError(err.message || 'Proof with OCR failed');
    } finally {
      setLoading(false);
    }
  };

  if (!transcriptionText.trim()) {
    return (
      <div className="card p-5 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          OCR Correction Analysis
        </h3>
        <p className="text-xs text-slate-400">
          Enter AGC transcription text in the editor to analyze for OCR errors
        </p>
      </div>
    );
  }

  return (
    <div className="card p-5 space-y-4">
      <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
        <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        OCR Correction Analysis
      </h3>

      <div className="flex gap-2">
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="flex-1 py-2 px-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold shadow transition disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze OCR Errors'}
        </button>
        <button
          onClick={handleProofWithOcr}
          disabled={loading}
          className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition border border-slate-700"
          title="Run proofing with automatic OCR preprocessing"
        >
          Proof with OCR
        </button>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/60 p-3 rounded text-xs text-rose-300">
          {error}
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-900/50 border border-slate-700/50 rounded p-3">
            <div className="text-slate-400">Total Lines</div>
            <div className="text-white font-mono">{summary.total_lines}</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/50 rounded p-3">
            <div className="text-slate-400">Corrections Found</div>
            <div className="text-white font-mono">{summary.corrections_found}</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/50 rounded p-3">
            <div className="text-slate-400">Overall Confidence</div>
            <div className="text-white font-mono">{(summary.overall_confidence * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-700/50 rounded p-3">
            <div className="text-slate-400">Patterns Detected</div>
            <div className="text-white font-mono">{Object.keys(summary.pattern_breakdown).length}</div>
          </div>
        </div>
      )}

      {result && result.corrections.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Detected Corrections</h4>
          <div className="max-h-64 overflow-auto space-y-2 border border-slate-700/50 rounded bg-slate-900/30 p-3">
            {result.corrections.map((corr, idx) => (
              <div key={idx} className="text-xs font-mono space-y-1 p-2 bg-slate-950/50 rounded border border-slate-800/50">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-cyan-400">Line {corr.line_number}</span>
                  <span className="text-slate-500">Col {corr.column_start}-{corr.column_end}</span>
                  <span className="text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">{corr.pattern_description}</span>
                  <span className="text-amber-400 ml-auto">Conf: {(corr.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="text-slate-300">
                  <span className="text-rose-400 line-through">{corr.original_text}</span>
                  <span className="text-emerald-400 ml-2">→</span>
                  <span className="text-emerald-400 ml-2">{corr.corrected_text}</span>
                </div>
                <div className="text-slate-500 truncate">{corr.context}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result && result.corrections.length === 0 && (
        <div className="text-center py-4 text-slate-500 text-xs">
          No OCR errors detected in transcription
        </div>
      )}

      {result && result.corrections.length > 0 && (
        <div className="pt-2 border-t border-slate-700/50">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Corrected Text Preview</h4>
          <div className="flex gap-2 mb-2">
            <button
              onClick={handleApply}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow transition border border-emerald-600/30"
            >
              Apply to Editor
            </button>
          </div>
          <div className="font-mono text-xs bg-slate-950 border border-slate-700/50 rounded p-3 max-h-40 overflow-auto text-slate-200 whitespace-pre-wrap">
            {result.corrected_text}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { ScanMetadata, DiscrepancyScanReference } from '../api/client';
import { api } from '../api/client';

interface Props {
  programId: string;
  discrepancies?: Array<{ line_number: number }>;
}

export const ScanReferencePanel: React.FC<Props> = ({ programId, discrepancies = [] }) => {
  const [scanMetadata, setScanMetadata] = useState<ScanMetadata | null>(null);
  const [discrepancyRefs, setDiscrepancyRefs] = useState<Record<number, DiscrepancyScanReference>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadScanData() {
      setLoading(true);
      setError(null);
      try {
        const meta = await api.getScanReference(programId);
        setScanMetadata(meta);
        if (discrepancies.length > 0) {
          const refs: Record<number, DiscrepancyScanReference> = {};
          for (const disc of discrepancies) {
            try {
              const ref = await api.getDiscrepancyScanReference(programId, disc.line_number);
              refs[disc.line_number] = ref;
            } catch { /* ignore individual failures */ }
          }
          setDiscrepancyRefs(refs);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load scan references');
      } finally {
        setLoading(false);
      }
    }
    loadScanData();
  }, [programId, discrepancies]);

  if (loading) return <div className="card p-4 text-center text-slate-400"><div className="flex items-center justify-center gap-2"><div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div><span className="text-sm">Loading scan references...</span></div></div>;
  if (error) return <div className="card p-4 text-center text-rose-400"><p className="text-sm">⚠️ {error}</p><p className="text-xs text-slate-400 mt-1">Scan references may be unavailable offline</p></div>;
  if (!scanMetadata) return <div className="card p-4 text-center text-slate-400"><p className="text-sm">No scan references found for this program</p></div>;

  return (
    <div className="card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-cyan-900/50 border border-cyan-700 flex items-center justify-center text-cyan-300 text-xs">📄</span>
          Historical Scan References
        </h3>
        <span className="text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded">{scanMetadata.source_type.toUpperCase()}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div><span className="text-slate-400">Program:</span><span className="text-slate-200 ml-2 font-mono">{scanMetadata.program_name}</span></div>
        <div><span className="text-slate-400">Craft:</span><span className="text-slate-200 ml-2">{scanMetadata.craft}</span></div>
        <div><span className="text-slate-400">Source:</span><span className="text-slate-200 ml-2">{scanMetadata.source}</span></div>
        <div><span className="text-slate-400">Fetched:</span><span className="text-slate-200 ml-2">{new Date(scanMetadata.fetched_at).toLocaleString()}</span></div>
      </div>

      {scanMetadata.pages.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Available Scan Pages</h4>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {scanMetadata.pages.map((page) => (
              <div key={page.range_key} className="bg-slate-900/50 border border-slate-700/50 rounded p-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-slate-200 truncate font-mono">{page.description}</div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-2">
                      {page.start_page > 0 && <>Pages {page.start_page}–{page.end_page}<span className="text-slate-500">|</span></>}
                      <span className="px-1.5 py-0.5 bg-slate-700 rounded text-[10px]">{page.quality}</span>
                    </div>
                  </div>
                  <a href={page.url} target="_blank" rel="noopener noreferrer" className="text-xs text-cyan-400 hover:text-cyan-300 font-mono whitespace-nowrap px-2 py-1 bg-cyan-900/20 border border-cyan-800 rounded flex-shrink-0">View Scan →</a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {discrepancies.length > 0 && (
        <div className="border-t border-slate-700 pt-4 space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Discrepancy Scan References ({discrepancies.length})</h4>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {discrepancies.map((disc) => {
              const ref = discrepancyRefs[disc.line_number];
              return (
                <div key={disc.line_number} className="bg-slate-900/50 border border-slate-700/50 rounded p-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded">Line {disc.line_number}</span>
                      {ref && (
                        <>
                          {ref.estimated_scan_page && <span className="text-xs text-slate-200">→ Est. Page <span className="font-mono text-cyan-400">{ref.estimated_scan_page}</span></span>}
                          {ref.scan_url && <a href={ref.scan_url} target="_blank" rel="noopener noreferrer" className="text-xs text-cyan-400 hover:text-cyan-300">Open Scan</a>}
                        </>
                      )}
                    </div>
                    {ref && ref.note && <span className="text-[10px] text-slate-500 italic truncate max-w-xs">{ref.note}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="text-[10px] text-slate-500 border-t border-slate-700 pt-2">
        <span className="font-mono">{scanMetadata.scan_base_url}</span>
        <span className="ml-2">(Source: {scanMetadata.source_type})</span>
      </div>
    </div>
  );
};
import React, { useMemo } from 'react';
import { ProgramComparisonResult, DiffChange } from '../api/client';

interface Props {
  comparison: ProgramComparisonResult | null;
  loading: boolean;
}

export const ComparisonViewer: React.FC<Props> = ({ comparison, loading }) => {
  if (loading) return <div className="card p-6 text-center text-slate-400"><div className="flex items-center justify-center gap-2"><div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div><span>Comparing Luminary vs Comanche variants...</span></div></div>;

  if (!comparison) return <div className="card p-6 text-center text-slate-400"><div className="w-12 h-12 mx-auto mb-3 text-slate-700">📊</div><h3 className="text-lg font-semibold text-slate-300 mb-2">No Comparison Data</h3><p className="text-sm text-slate-500 max-w-md mx-auto">Select a program and click "Compare Variants" to see the LM vs CM side-by-side diff.</p></div>;


  // Summary stats
  const summary = comparison.summary;
  const totalChanges = (summary.added || 0) + (summary.removed || 0) + (summary.modified || 0);

  // Group diff by type for display
  const diffByType = useMemo(() => {
    const groups: Record<string, DiffChange[]> = {
      added: [],
      removed: [],
      modified: [],
      unchanged: []
    };
    comparison.diff.forEach(d => {
      if (groups[d.type]) groups[d.type].push(d);
    });
    return groups;
  }, [comparison.diff]);

  const getChangeColor = (type: string) => {
    switch (type) {
      case 'added': return 'text-emerald-400 bg-emerald-950/30 border-emerald-800/30';
      case 'removed': return 'text-rose-400 bg-rose-950/30 border-rose-800/30';
      case 'modified': return 'text-amber-400 bg-amber-950/30 border-amber-800/30';
      default: return 'text-slate-500 bg-slate-800/30 border-slate-700/30';
    }
  };

  const getCategoryBadge = (category: string | null | undefined) => {
    if (!category) return null;
    const badges: Record<string, string> = {
      'opcode': 'bg-blue-900/50 text-blue-300 border-blue-800',
      'operand': 'bg-purple-900/50 text-purple-300 border-purple-800',
      'register': 'bg-cyan-900/50 text-cyan-300 border-cyan-800',
      'bank': 'bg-orange-900/50 text-orange-300 border-orange-800',
      'label': 'bg-pink-900/50 text-pink-300 border-pink-800',
      'comment': 'bg-slate-800 text-slate-400 border-slate-700',
      'structure': 'bg-amber-900/50 text-amber-300 border-amber-800'
    };
    return badges[category] || 'bg-slate-800 text-slate-400 border-slate-700';
  };

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
        <div>
          <h3 className="text-xl font-semibold text-white">Luminary vs Comanche Program Comparison</h3>
          <p className="text-xs text-slate-400">
            AST-level semantic diff of Apollo 11 guidance computer variants
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${summary.added > 0 ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/40' : 'bg-slate-800 text-slate-500'}`}>
            +{summary.added || 0}
          </span>
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${summary.removed > 0 ? 'bg-rose-950/40 text-rose-400 border border-rose-800/40' : 'bg-slate-800 text-slate-500'}`}>
            -{summary.removed || 0}
          </span>
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${summary.modified > 0 ? 'bg-amber-950/40 text-amber-400 border border-amber-800/40' : 'bg-slate-800 text-slate-500'}`}>
            ~{summary.modified || 0}
          </span>
          <span className="px-2.5 py-1 text-xs rounded-full font-medium bg-slate-800 text-slate-400 border border-slate-700">
            ={summary.unchanged || 0}
          </span>
          <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
            {comparison.program_name} ({comparison.program_id})
          </span>
        </div>
      </div>

      {/* Semantic Divergences Panel */}
      {comparison.semantic_divergences.length > 0 && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 space-y-3">
          <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 16h.01" />
            </svg>
            Semantic Divergences ({comparison.semantic_divergences.length})
          </h4>
          <div className="space-y-2">
            {comparison.semantic_divergences.map((div, idx) => (
              <div key={idx} className="bg-slate-950/50 p-3 rounded border border-slate-800/50">
                <div className="flex items-start gap-2">
                  <span className={`px-1.5 py-0.5 text-[10px] font-mono rounded border ${div.severity === 'high' ? 'bg-rose-950/50 text-rose-400 border-rose-800' : div.severity === 'medium' ? 'bg-amber-950/50 text-amber-400 border-amber-800' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                    {div.severity?.toUpperCase() || 'LOW'}
                  </span>
                  <span className="text-xs font-medium text-slate-300 capitalize">{div.type.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{div.description}</p>
                {(div.lm_value || div.cm_value) && (
                  <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] font-mono">
                    <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                      <span className="text-blue-400">LM:</span> {Array.isArray(div.lm_value) ? div.lm_value.join(', ') : div.lm_value}
                    </div>
                    <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                      <span className="text-orange-400">CM:</span> {Array.isArray(div.cm_value) ? div.cm_value.join(', ') : div.cm_value}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Side-by-side Diff View */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-slate-200">Instruction-Level Diff</h4>
        
        {/* Added */}
        {diffByType.added.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-xs font-medium text-emerald-400 uppercase tracking-wider">
              Added in Comanche ({diffByType.added.length})
            </h5>
            {diffByType.added.map((change, idx) => (
              <div key={idx} className={`p-3 rounded border ${getChangeColor('added')}`}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono text-slate-400">Line {change.line_number_cm}</span>
                  {change.change_category && (
                    <span className={`px-1.5 py-0.5 text-[10px] rounded border ${getCategoryBadge(change.change_category)}`}>
                      {change.change_category}
                    </span>
                  )}
                </div>
                <div className="font-mono text-xs text-emerald-300">
                  + {change.cm_instruction?.opcode} {change.cm_instruction?.operand || ''}
                  {change.cm_instruction?.label && <span className="text-cyan-400 ml-1">{change.cm_instruction.label}:</span>}
                </div>
                <p className="text-[10px] text-slate-500 mt-1">{change.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Removed */}
        {diffByType.removed.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-xs font-medium text-rose-400 uppercase tracking-wider">
              Removed from Comanche ({diffByType.removed.length})
            </h5>
            {diffByType.removed.map((change, idx) => (
              <div key={idx} className={`p-3 rounded border ${getChangeColor('removed')}`}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono text-slate-400">Line {change.line_number_lm}</span>
                  {change.change_category && (
                    <span className={`px-1.5 py-0.5 text-[10px] rounded border ${getCategoryBadge(change.change_category)}`}>
                      {change.change_category}
                    </span>
                  )}
                </div>
                <div className="font-mono text-xs text-rose-300 line-through">
                  - {change.lm_instruction?.opcode} {change.lm_instruction?.operand || ''}
                  {change.lm_instruction?.label && <span className="text-cyan-400 ml-1">{change.lm_instruction.label}:</span>}
                </div>
                <p className="text-[10px] text-slate-500 mt-1">{change.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Modified */}
        {diffByType.modified.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-xs font-medium text-amber-400 uppercase tracking-wider">
              Modified ({diffByType.modified.length})
            </h5>
            {diffByType.modified.map((change, idx) => (
              <div key={idx} className={`p-3 rounded border ${getChangeColor('modified')}`}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono text-slate-400">LM:{change.line_number_lm} → CM:{change.line_number_cm}</span>
                  {change.change_category && (
                    <span className={`px-1.5 py-0.5 text-[10px] rounded border ${getCategoryBadge(change.change_category)}`}>
                      {change.change_category}
                    </span>
                  )}
                </div>
                <div className="font-mono text-xs text-rose-300 line-through">
                  - {change.lm_instruction?.opcode} {change.lm_instruction?.operand || ''}
                </div>
                <div className="font-mono text-xs text-emerald-300">
                  + {change.cm_instruction?.opcode} {change.cm_instruction?.operand || ''}
                </div>
                <p className="text-[10px] text-slate-500 mt-1">{change.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Unchanged (collapsible) */}
        {diffByType.unchanged.length > 0 && (
          <details className="group">
            <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-300 flex items-center gap-2">
              <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Unchanged Instructions ({diffByType.unchanged.length}) - Click to expand
            </summary>
            <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
              {diffByType.unchanged.slice(0, 20).map((change, idx) => (
                <div key={idx} className={`p-2 rounded border ${getChangeColor('unchanged')}`}>
                  <div className="font-mono text-[10px] text-slate-400">
                    {change.lm_instruction?.label ? <span className="text-cyan-500">{change.lm_instruction.label}:</span> : null}
                    {change.lm_instruction?.opcode} {change.lm_instruction?.operand || ''}
                  </div>
                </div>
              ))}
              {diffByType.unchanged.length > 20 && (
                <div className="text-[10px] text-slate-500 text-center py-2">
                  ... and {diffByType.unchanged.length - 20} more unchanged instructions
                </div>
              )}
            </div>
          </details>
        )}

        {totalChanges === 0 && (
          <div className="bg-emerald-950/20 border border-emerald-800/40 p-4 rounded text-sm text-emerald-300 text-center">
            No differences detected. Luminary and Comanche variants are structurally identical for this routine.
          </div>
        )}
      </div>

      {/* Variant Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-700/60 pt-4">
        {comparison.luminary && (
          <div className="bg-slate-900/50 p-4 rounded border border-blue-800/30">
            <h5 className="text-xs font-semibold text-blue-400 mb-2 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              Luminary 099 (Lunar Module)
            </h5>
            <dl className="space-y-1 text-xs">
              <div className="flex justify-between">
                <dt className="text-slate-500">Instructions</dt>
                <dd className="text-slate-200 font-mono">{comparison.luminary.metadata.instruction_count || comparison.luminary.parsed_instructions.length}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Unique Labels</dt>
                <dd className="text-slate-200 font-mono">{comparison.luminary.metadata.unique_labels}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Banks Used</dt>
                <dd className="text-slate-200 font-mono">
                  {comparison.luminary.metadata.banks_used?.join(', ') || 'N/A'}
                </dd>
              </div>
            </dl>
          </div>
        )}
        {comparison.comanche && (
          <div className="bg-slate-900/50 p-4 rounded border border-orange-800/30">
            <h5 className="text-xs font-semibold text-orange-400 mb-2 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
              Comanche 055 (Command Module)
            </h5>
            <dl className="space-y-1 text-xs">
              <div className="flex justify-between">
                <dt className="text-slate-500">Instructions</dt>
                <dd className="text-slate-200 font-mono">{comparison.comanche.metadata.instruction_count || comparison.comanche.parsed_instructions.length}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Unique Labels</dt>
                <dd className="text-slate-200 font-mono">{comparison.comanche.metadata.unique_labels}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Banks Used</dt>
                <dd className="text-slate-200 font-mono">
                  {comparison.comanche.metadata.banks_used?.join(', ') || 'N/A'}
                </dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
};
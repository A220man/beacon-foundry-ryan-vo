import React from 'react';
import { TrajectoryStep } from '../api/client';

interface Props {
  trajectory: TrajectoryStep[];
  burnProgram: string;
  deltaV: number;
  maxAttitudeRate: number;
  anomalyDetected: boolean;
  notes: string[];
}

export const TrajectoryPlot: React.FC<Props> = ({
  trajectory, burnProgram, deltaV, maxAttitudeRate, anomalyDetected, notes
}) => {
  if (!trajectory.length) return <div className="card p-6 text-center text-slate-400">No trajectory data. Configure parameters and run a simulation.</div>;

  const maxAlt = Math.max(...trajectory.map(t => t.altitude_m), 1);
  const maxVel = Math.max(...trajectory.map(t => t.velocity_mps), 1);

  return (
    <div className="card p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
        <div><h3 className="text-xl font-semibold text-white">Guidance Trajectory — {burnProgram}</h3><p className="text-xs text-slate-400">Discrete state-vector simulation with anomaly detection</p></div>
        <div className="flex flex-wrap gap-3 text-xs">
          <span className="bg-slate-800 px-2 py-1 rounded"><span className="font-semibold text-cyan-400">ΔV: </span>{deltaV.toFixed(1)} m/s</span>
          <span className="bg-slate-800 px-2 py-1 rounded"><span className="font-semibold text-amber-400">Max Pitch Rate: </span>{maxAttitudeRate.toFixed(2)}°/s</span>
          <span className={`px-2 py-1 rounded ${anomalyDetected ? 'bg-rose-900/50 text-rose-300' : 'bg-emerald-900/50 text-emerald-300'}`}>
            {anomalyDetected ? '⚠️ Anomaly Detected' : '✓ Nominal'}
          </span>
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-xs text-slate-400 flex justify-between"><span>Altitude (m)</span><span>Velocity (m/s)</span></div>
        <svg width="100%" height="180" viewBox="0 0 600 180" className="bg-slate-900/50 rounded border border-slate-800">
          <polyline fill="none" stroke="#22d3ee" strokeWidth="2" points={trajectory.map((t, i) => `${(i / Math.max(trajectory.length - 1, 1)) * 590},${170 - (t.altitude_m / maxAlt) * 160}`).join(' ')} />
          <polyline fill="none" stroke="#f472b6" strokeWidth="2" points={trajectory.map((t, i) => `${(i / Math.max(trajectory.length - 1, 1)) * 590},${170 - (t.velocity_mps / maxVel) * 160}`).join(' ')} />
          <text x="10" y="15" fontSize="10" fill="#64748b">Cyan: Altitude | Pink: Velocity</text>
        </svg>
      </div>

      <div className="overflow-x-auto max-h-56 overflow-y-auto border border-slate-800 rounded">
        <table className="w-full text-xs border-collapse"><thead><tr className="bg-slate-800 text-left text-slate-400"><th className="p-2">t(s)</th><th className="p-2">Altitude</th><th className="p-2">Velocity</th><th className="p-2">Pitch</th><th className="p-2">Thrust</th><th className="p-2">Fuel</th><th className="p-2">Anomaly</th></tr></thead><tbody>
          {trajectory.filter((_, i) => i % Math.max(1, Math.floor(trajectory.length / 15)) === 0).map(t => (
            <tr key={t.timestamp_s} className={t.anomaly_flag ? 'bg-rose-900/20' : 'border-t border-slate-800/50'}><td className="p-2 font-mono">{t.timestamp_s.toFixed(0)}</td><td className="p-2">{t.altitude_m.toFixed(0)}</td><td className="p-2">{t.velocity_mps.toFixed(1)}</td><td className="p-2">{t.attitude_pitch_deg.toFixed(1)}</td><td className="p-2">{t.thrust_pct.toFixed(0)}%</td><td className="p-2">{t.fuel_remaining_kg.toFixed(0)}</td><td className="p-2">{t.anomaly_flag ? '⚠️' : ''}</td></tr>
          ))}
        </tbody></table>
      </div>
      {notes.length && <div className="bg-slate-900/70 p-3 rounded border border-slate-800"><h4 className="text-xs font-semibold text-slate-300 mb-1">Operational Notes</h4><ul className="text-xs text-slate-300 space-y-1 pl-4">{notes.map((n, i) => <li key={i}>• {n}</li>)}</ul></div>}
    </div>
  );
};
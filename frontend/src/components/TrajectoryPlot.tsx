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
  trajectory,
  burnProgram,
  deltaV,
  maxAttitudeRate,
  anomalyDetected,
  notes
}) => {
  if (trajectory.length === 0) {
    return (
      <div className="card p-6 text-center text-slate-400">
        No trajectory simulation data. Configure parameters and run a simulation.
      </div>
    );
  }

  // Calculate scaling for altitude chart
  const maxAlt = Math.max(...trajectory.map(t => t.altitude_m), 1);
  const maxVel = Math.max(...trajectory.map(t => t.velocity_mps), 1);

  return (
    <div className="card p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
        <div>
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <span>Burn Telemetry:</span>
            <span className="font-mono text-cyan-400">{burnProgram}</span>
          </h3>
          <p className="text-xs text-slate-400">
            Dynamical 6-DOF state integration and RCS reaction jet phase maintenance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
            anomalyDetected 
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' 
              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          }`}>
            {anomalyDetected ? 'ANOMALY DETECTED' : 'NOMINAL CORRIDOR'}
          </span>
          <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
            Total Δv: {deltaV} m/s
          </span>
          <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
            Max Attitude Rate: {maxAttitudeRate}°/s
          </span>
        </div>
      </div>

      {/* SVG Trajectory Chart */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-400 font-mono">
          <span>Altitude (m) vs Time (s) [White]</span>
          <span>Velocity (m/s) [Cyan]</span>
        </div>
        <div className="w-full h-48 bg-slate-900 rounded-lg border border-slate-800 p-2 relative">
          <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
            {/* Grid lines */}
            <line x1="0" y1="25" x2="100" y2="25" stroke="#334155" strokeWidth="0.5" strokeDasharray="2" />
            <line x1="0" y1="50" x2="100" y2="50" stroke="#334155" strokeWidth="0.5" strokeDasharray="2" />
            <line x1="0" y1="75" x2="100" y2="75" stroke="#334155" strokeWidth="0.5" strokeDasharray="2" />

            {/* Altitude line (white) */}
            <polyline
              fill="none"
              stroke="#f8fafc"
              strokeWidth="2"
              points={trajectory.map((pt, i) => {
                const x = (i / (trajectory.length - 1)) * 100;
                const y = 100 - (pt.altitude_m / maxAlt) * 90;
                return `${x},${y}`;
              }).join(' ')}
            />

            {/* Velocity line (cyan) */}
            <polyline
              fill="none"
              stroke="#22d3ee"
              strokeWidth="1.5"
              strokeDasharray="1"
              points={trajectory.map((pt, i) => {
                const x = (i / (trajectory.length - 1)) * 100;
                const y = 100 - (pt.velocity_mps / maxVel) * 90;
                return `${x},${y}`;
              }).join(' ')}
            />
          </svg>
        </div>
      </div>

      {/* Trajectory Data Table Sample */}
      <div className="overflow-x-auto max-h-56 overflow-y-auto border border-slate-800 rounded">
        <table className="w-full text-left text-xs font-mono text-slate-300">
          <thead className="bg-slate-900/80 sticky top-0 text-slate-400 uppercase">
            <tr>
              <th className="py-2 px-3">T (s)</th>
              <th className="py-2 px-3">Altitude</th>
              <th className="py-2 px-3">Velocity</th>
              <th className="py-2 px-3">Thrust</th>
              <th className="py-2 px-3">Pitch</th>
              <th className="py-2 px-3">Thrusters</th>
              <th className="py-2 px-3">State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {trajectory.slice(0, 15).map(step => (
              <tr key={step.timestamp_s} className={step.anomaly_flag ? 'bg-rose-950/20' : ''}>
                <td className="py-1.5 px-3">+{step.timestamp_s}s</td>
                <td className="py-1.5 px-3">{step.altitude_m}m</td>
                <td className="py-1.5 px-3">{step.velocity_mps}m/s</td>
                <td className="py-1.5 px-3">{step.thrust_pct}%</td>
                <td className="py-1.5 px-3">{step.attitude_pitch_deg}°</td>
                <td className="py-1.5 px-3">{step.active_thrusters.join(', ')}</td>
                <td className="py-1.5 px-3">
                  {step.anomaly_flag ? (
                    <span className="text-rose-400 font-bold">PERTURBATION</span>
                  ) : (
                    <span className="text-emerald-400">STABLE</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Operational notes */}
      {notes.length > 0 && (
        <div className="bg-slate-900/70 p-3 rounded border border-slate-800">
          <h4 className="text-xs uppercase tracking-wide text-slate-400 font-semibold mb-1">Mission Notes</h4>
          <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
            {notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

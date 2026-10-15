import React, { useState, useEffect } from 'react';
import {
  api, AGCProgramSummary, ProofResult, TrajectorySimulationResponse,
  MLEvalResult, AdvisoryResponse, AuthConfig,
  ProgramComparisonResult
} from './api/client';
import { ProofViewer } from './components/ProofViewer';
import { TrajectoryPlot } from './components/TrajectoryPlot';
import { BenchmarkDashboard } from './components/BenchmarkDashboard';
import { AdvisoryModal } from './components/AdvisoryModal';
import { ComparisonViewer } from './components/ComparisonViewer';

export const App: React.FC = () => {
  // Navigation / Tabs
  const [activeTab, setActiveTab] = useState<'proofing' | 'trajectory' | 'benchmark' | 'audit' | 'comparison'>('proofing');

  // Auth State
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [user, setUser] = useState<{ username: string; roles: string[] } | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Programs & Proofing State
  const [programs, setPrograms] = useState<AGCProgramSummary[]>([]);
  const [selectedProgramId, setSelectedProgramId] = useState<string>('luminary099-waitlist');
  const [transcriptionInput, setTranscriptionInput] = useState<string>(
    `CA TIME1\nTC CHECKTIM\nCCS WAITEXIT\nTCF +2\nTC TASKOVER\nCHECKTIM INDEX Q\nCA 0\nAD ITEMP1\nTS L\nTC WAITLOOP\nTASKOVER EXTEND\nDTCB`
  );
  const [proofResult, setProofResult] = useState<ProofResult | null>(null);
  const [proofLoading, setProofLoading] = useState<boolean>(false);

  // Trajectory Simulation State
  const [burnProgram, setBurnProgram] = useState<string>('P63_BRAKING');
  const [altitude, setAltitude] = useState<number>(15000);
  const [velocity, setVelocity] = useState<number>(1690);
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false);
  const [trajectoryRes, setTrajectoryRes] = useState<TrajectorySimulationResponse | null>(null);
  const [trajLoading, setTrajLoading] = useState<boolean>(false);

  // Benchmark State
  const [benchResult, setBenchResult] = useState<MLEvalResult | null>(null);
  const [benchLoading, setBenchLoading] = useState<boolean>(false);

  // Advisory State
  const [advisoryResult, setAdvisoryResult] = useState<AdvisoryResponse | null>(null);
  const [advisoryLoading, setAdvisoryLoading] = useState<boolean>(false);
  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<any>(null);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  // Comparison State
  const [comparisonResult, setComparisonResult] = useState<ProgramComparisonResult | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState<boolean>(false);

  // Init auth and configuration
  useEffect(() => {
    async function init() {
      try {
        const conf = await api.getAuthConfig();
        setAuthConfig(conf);
        if (conf.auth_mode === 'local_demo') {
          // Auto login to local demo
          const loginRes = await api.demoLogin();
          setUser({ username: loginRes.username, roles: loginRes.roles });
          loadPrograms();
        }
      } catch (err: any) {
        setAuthError(err.message || 'Initialization failed');
      }
    }
    init();
  }, []);

  async function loadPrograms() {
    try {
      const res = await api.getPrograms();
      setPrograms(res.programs);
    } catch (err: any) {
      console.error(err);
    }
  }

  async function handleProof() {
    setProofLoading(true);
    setAuthError(null);
    try {
      const res = await api.executeProof(transcriptionInput);
      setProofResult(res);
    } catch (err: any) {
      setAuthError(err.message || 'Proofing execution failed');
    } finally {
      setProofLoading(false);
    }
  }

  async function handleSimulate() {
    setTrajLoading(true);
    setAuthError(null);
    try {
      const res = await api.simulateTrajectory(burnProgram, altitude, velocity, 60, simulateFailure);
      setTrajectoryRes(res);
    } catch (err: any) {
      setAuthError(err.message || 'Simulation execution failed');
    } finally {
      setTrajLoading(false);
    }
  }

  async function handleRunBenchmark() {
    setBenchLoading(true);
    setAuthError(null);
    try {
      const res = await api.runBenchmark();
      setBenchResult(res);
    } catch (err: any) {
      setAuthError(err.message || 'Benchmark evaluation failed');
    } finally {
      setBenchLoading(false);
    }
  }

  async function handleRequestAdvisory(query: string) {
    setAdvisoryLoading(true);
    try {
      const res = await api.requestAdvisory(
        selectedDiscrepancy ? 'PROOFING_DISCREPANCY' : 'GENERAL_INQUIRY',
        selectedDiscrepancy || { source: transcriptionInput.slice(0, 100) },
        query
      );
      setAdvisoryResult(res);
    } catch (err: any) {
      setAuthError(err.message || 'Advisory request failed');
    } finally {
      setAdvisoryLoading(false);
    }
  }

  async function loadAuditLogs() {
    try {
      const res = await api.getAuditLogs(50, 0);
      setAuditLogs(res.logs);
    } catch (err: any) {
      setAuthError(err.message || 'Failed to fetch audit log');
    }
  }
  async function handleCompare() {
    setComparisonLoading(true);
    setAuthError(null);
    try {
      const res = await api.compareProgramVariants(selectedProgramId);
      setComparisonResult(res);
    } catch (err: any) {
      setAuthError(err.message || 'Comparison failed');
    } finally {
      setComparisonLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-cyan-600 flex items-center justify-center font-bold text-white shadow">
            BF
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Beacon Foundry
              <span className="text-xs font-normal text-slate-400">| Ryan Vo | AI & Machine Learning</span>
            </h1>
            <p className="text-xs text-slate-400">
              Apollo Guidance Computer Telemetry & ML Proofing Platform
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span className="text-slate-300 font-medium">{user.username}</span>
              <span className="text-slate-500 font-mono">[{user.roles.join(', ')}]</span>
            </div>
          ) : (
            <button
              onClick={() => api.demoLogin().then(l => setUser({ username: l.username, roles: l.roles }))}
              className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold rounded text-white"
            >
              Authenticate (Local Demo)
            </button>
          )}

          <div className="text-xs text-slate-500 border-l border-slate-700 pl-4 flex items-center gap-2">
            <span>{authConfig ? authConfig.auth_mode : 'initializing'}</span>
            <span>v1.0.0</span>
          </div>
        </div>
      </header>

      {/* Navigation tabs */}
      <nav className="bg-slate-900 border-b border-slate-800 px-6 flex gap-2">
        <button
          onClick={() => setActiveTab('proofing')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition ${
            activeTab === 'proofing'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          AGC Proofing & AST
        </button>
        <button
          onClick={() => setActiveTab('trajectory')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition ${
            activeTab === 'trajectory'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Guidance Trajectory
        </button>
        <button
          onClick={() => setActiveTab('benchmark')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition ${
            activeTab === 'benchmark'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          ML Alignment Benchmark
        </button>
        <button
          onClick={() => { setActiveTab('audit'); loadAuditLogs(); }}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition ${
            activeTab === 'audit'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Audit Logs
        </button>

        <button
          onClick={() => { setActiveTab('comparison'); handleCompare(); }}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition ${
            activeTab === 'comparison'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          LM vs CM Comparison
        </button>
      </nav>

      {/* Main Content Body */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        {authError && (
          <div className="bg-rose-950/40 border border-rose-800/60 p-4 rounded text-xs text-rose-300">
            ⚠️ {authError}
          </div>
        )}

        {/* Tab 1: Proofing & AST */}
        {activeTab === 'proofing' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-4">
              <div className="card p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-200">Transcription Input</h3>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">Select Historical Routine:</label>
                  <select
                    value={selectedProgramId}
                    onChange={e => setSelectedProgramId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-200"
                  >
                    {programs.length > 0 ? (
                      programs.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name} [{p.craft}]
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="luminary099-waitlist">Luminary 099 WAITLIST</option>
                        <option value="luminary099-pflite">Luminary 099 POWERED_FLIGHT</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">AGC Source Text:</label>
                  <textarea
                    rows={12}
                    value={transcriptionInput}
                    onChange={e => setTranscriptionInput(e.target.value)}
                    className="w-full font-mono text-xs bg-slate-900 border border-slate-700 rounded p-3 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleProof}
                    disabled={proofLoading}
                    className="flex-1 py-2 px-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold shadow transition disabled:opacity-50"
                  >
                    {proofLoading ? 'Analyzing AST...' : 'Execute AST Proofing'}
                  </button>
                  <button
                    onClick={() => {
                      setTranscriptionInput(
                        "CA TIME1\nTX CHECKTIM\nCCS WAITEXIT\nTCF +2\nTS\nCHECKTIM INDEX Q\nCA 0\nAD ITEMP1\nTS L"
                      );
                    }}
                    className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition border border-slate-700"
                    title="Load snippet with known OCR anomalies"
                  >
                    Load Anomaly Sample
                  </button>
                </div>
              </div>

              {/* Advisory Assistant */}
              <AdvisoryModal
                advisory={advisoryResult}
                loading={advisoryLoading}
                onRequestAdvisory={handleRequestAdvisory}
              />
            </div>

            <div className="lg:col-span-2">
              <ProofViewer
                result={proofResult}
                onAdvisoryRequest={disc => {
                  setSelectedDiscrepancy(disc);
                  handleRequestAdvisory(`Investigate line ${disc.line_number}: ${disc.issue_type} - ${disc.suggestion}`);
                }}
              />
            </div>
          </div>
        )}

        {/* Tab 2: Guidance Trajectory Simulation */}
        {activeTab === 'trajectory' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-4">
              <div className="card p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-200">Simulation Configuration</h3>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">Burn Program Phase:</label>
                  <select
                    value={burnProgram}
                    onChange={e => setBurnProgram(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-200"
                  >
                    <option value="P63_BRAKING">P63 - Braking Phase (Descent Engine 95%)</option>
                    <option value="P64_APPROACH">P64 - Approach Phase (Visibility Corridor)</option>
                    <option value="P66_TERMINAL">P66 - Terminal Landing (Manual Rate of Descent)</option>
                    <option value="TJET_REACTION">TJET - Reaction Control Jet Law</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">Initial Altitude (meters):</label>
                  <input
                    type="number"
                    value={altitude}
                    onChange={e => setAltitude(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">Initial Velocity (m/s):</label>
                  <input
                    type="number"
                    value={velocity}
                    onChange={e => setVelocity(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-200"
                  />
                </div>

                <div className="pt-2">
                  <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={simulateFailure}
                      onChange={e => setSimulateFailure(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-700 text-cyan-600 focus:ring-0"
                    />
                    Inject Thruster Jet Failure Perturbation
                  </label>
                </div>

                <button
                  onClick={handleSimulate}
                  disabled={trajLoading}
                  className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold shadow transition disabled:opacity-50"
                >
                  {trajLoading ? 'Integrating State Vectors...' : 'Simulate Trajectory'}
                </button>
              </div>
            </div>

            <div className="lg:col-span-2">
              <TrajectoryPlot
                trajectory={trajectoryRes ? trajectoryRes.trajectory : []}
                burnProgram={trajectoryRes ? trajectoryRes.burn_program : burnProgram}
                deltaV={trajectoryRes ? trajectoryRes.delta_v_total : 0}
                maxAttitudeRate={trajectoryRes ? trajectoryRes.max_attitude_rate_deg_s : 0}
                anomalyDetected={trajectoryRes ? trajectoryRes.anomaly_detected : false}
                notes={trajectoryRes ? trajectoryRes.notes : []}
              />
            </div>
          </div>
        )}

        {/* Tab 3: ML Alignment Benchmark */}
        {activeTab === 'benchmark' && (
          <div>
            <BenchmarkDashboard
              result={benchResult}
              loading={benchLoading}
              onRunBenchmark={handleRunBenchmark}
            />
          </div>
        )}

        {/* Tab 4: Audit Logs */}
        {activeTab === 'audit' && (
          <div className="card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
              <h3 className="text-xl font-semibold text-white">System Audit Trail</h3>
              <button
                onClick={loadAuditLogs}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 rounded border border-slate-700"
              >
                Refresh Log
              </button>
            </div>

            <div className="overflow-x-auto border border-slate-800 rounded">
              <table className="w-full text-left text-xs font-mono text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase">
                  <tr>
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Timestamp (UTC)</th>
                    <th className="py-2.5 px-3">User</th>
                    <th className="py-2.5 px-3">Action</th>
                    <th className="py-2.5 px-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-slate-500">
                        No audit events recorded yet.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map(l => (
                      <tr key={l.id} className="hover:bg-slate-900/40">
                        <td className="py-2 px-3">{l.id}</td>
                        <td className="py-2 px-3 text-slate-400">{l.timestamp}</td>
                        <td className="py-2 px-3 text-cyan-400">{l.user_id}</td>
                        <td className="py-2 px-3 font-semibold text-white">{l.action}</td>
                        <td className="py-2 px-3 text-slate-400 max-w-md truncate">{l.details}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {/* Tab 5: LM vs CM Comparison */}
        {activeTab === 'comparison' && (
          <div>
            <ComparisonViewer
              comparison={comparisonResult}
              loading={comparisonLoading}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 px-6 text-xs text-slate-500 flex flex-wrap justify-between items-center gap-2 mt-auto">
        <div>
          Beacon Foundry © 2026 Ryan Vo &lt;<a href="mailto:ryandtvo@gmail.com" className="text-slate-400 hover:underline">ryandtvo@gmail.com</a>&gt;
        </div>
        <div>
          GitHub: <a href="https://github.com/A220man" target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">A220man</a>
        </div>
      </footer>
    </div>
  );
};

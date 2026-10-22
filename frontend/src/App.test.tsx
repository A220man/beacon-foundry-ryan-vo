import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from './App';
import { ProofViewer } from './components/ProofViewer';
import { TrajectoryPlot } from './components/TrajectoryPlot';
import { BenchmarkDashboard } from './components/BenchmarkDashboard';
import { api } from './api/client';

describe('Beacon Foundry Frontend Components', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders application header and title', async () => {
    vi.spyOn(api, 'getAuthConfig').mockResolvedValue({
      auth_mode: 'local_demo',
      keycloak_url: 'http://localhost:8080',
      keycloak_realm: 'beacon-realm',
      keycloak_client_id: 'beacon-client'
    });
    vi.spyOn(api, 'demoLogin').mockResolvedValue({
      access_token: 'demo-token',
      token_type: 'bearer',
      username: 'flight-analyst',
      roles: ['viewer', 'operator']
    });
    vi.spyOn(api, 'getPrograms').mockResolvedValue({ programs: [] });

    render(<App />);

    expect(screen.getAllByText(/Beacon Foundry/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Ryan Vo/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/AGC Proofing & AST/i)).toBeInTheDocument();
  });

  it('renders ProofViewer with discrepancies correctly', () => {
    const mockResult = {
      total_lines: 10,
      parsed_instructions: 8,
      discrepancies: [
        {
          line_number: 2,
          issue_type: 'OPCODE_MISMATCH',
          scanned_text: 'TC CHECKTIM',
          transcribed_text: 'TX CHECKTIM',
          confidence: 0.95,
          suggestion: 'Unrecognized opcode TX'
        }
      ],
      quality_score: 0.875,
      status: 'DISCREPANCIES_DETECTED'
    };

    render(<ProofViewer result={mockResult} />);

    expect(screen.getByText(/AGC Microfilm Proofing Report/i)).toBeInTheDocument();
    expect(screen.getByText(/DISCREPANCIES_DETECTED/i)).toBeInTheDocument();
    expect(screen.getByText(/Line 2/i)).toBeInTheDocument();
    expect(screen.getByText(/TX CHECKTIM/i)).toBeInTheDocument();
  });

  it('renders TrajectoryPlot with attitude rate and flight corridor status', () => {
    const mockTrajectory = [
      {
        timestamp_s: 0,
        altitude_m: 15000,
        velocity_mps: 1690,
        thrust_pct: 95,
        fuel_remaining_kg: 8200,
        active_thrusters: ['DESCENT_DPS'],
        attitude_pitch_deg: 45,
        anomaly_flag: false
      },
      {
        timestamp_s: 1,
        altitude_m: 14831,
        velocity_mps: 1680,
        thrust_pct: 95,
        fuel_remaining_kg: 8185,
        active_thrusters: ['DESCENT_DPS'],
        attitude_pitch_deg: 44.7,
        anomaly_flag: false
      }
    ];

    render(
      <TrajectoryPlot
        trajectory={mockTrajectory}
        burnProgram="P63_BRAKING"
        deltaV={120.5}
        maxAttitudeRate={0.3}
        anomalyDetected={false}
        notes={['Corridor nominal']}
      />
    );

    expect(screen.getByText(/P63_BRAKING/i)).toBeInTheDocument();
    expect(screen.getByText(/✓ Nominal/i)).toBeInTheDocument();
    expect(screen.getByText(/120\.5/)).toBeInTheDocument();
  });

  it('renders BenchmarkDashboard with ML metrics comparison', () => {
    const mockBenchmark = {
      timestamp: '2026-10-12T11:00:00Z',
      dataset_name: 'apollo11_bench',
      total_samples: 40,
      baseline_metrics: {
        precision: 0.81,
        recall: 0.85,
        f1_score: 0.83,
        roc_auc: 0.86,
        mean_latency_ms: 0.42
      },
      embedding_metrics: {
        precision: 0.94,
        recall: 0.90,
        f1_score: 0.92,
        roc_auc: 0.95,
        mean_latency_ms: 1.18
      },
      summary: 'Embedding Anomaly Model outperforms Baseline'
    };

    const runSpy = vi.fn();
    render(<BenchmarkDashboard result={mockBenchmark} loading={false} onRunBenchmark={runSpy} />);

    expect(screen.getByText(/AI\/ML Alignment Evaluation Suite/i)).toBeInTheDocument();
    expect(screen.getByText(/Embedding Anomaly Model outperforms Baseline/i)).toBeInTheDocument();
    expect(screen.getByText(/Embedding Cosine Model/i)).toBeInTheDocument();

    const btn = screen.getByRole('button', { name: /Run Evaluation Suite/i });
    fireEvent.click(btn);
    expect(runSpy).toHaveBeenCalled();
  });
});

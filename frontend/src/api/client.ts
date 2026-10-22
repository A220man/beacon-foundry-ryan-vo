export interface AGCInstruction {
  line_number: number;
  label?: string | null;
  opcode: string;
  operand?: string | null;
  comment?: string | null;
  raw: string;
}

export interface AGCProgramSummary {
  id: string;
  name: string;
  craft: string;
  description: string;
  created_at: string;
}

export interface AGCProgramDetail extends AGCProgramSummary {
  source_code: string;
  instructions: AGCInstruction[];
  source_lines_count: number;
}

export interface ProofDiscrepancy {
  line_number: number;
  issue_type: string;
  scanned_text: string;
  transcribed_text: string;
  confidence: number;
  suggestion: string;
}

export interface ProofResult {
  total_lines: number;
  parsed_instructions: number;
  discrepancies: ProofDiscrepancy[];
  quality_score: number;
  status: string;
}

export interface TrajectoryStep {
  timestamp_s: number;
  altitude_m: number;
  velocity_mps: number;
  thrust_pct: number;
  fuel_remaining_kg: number;
  active_thrusters: string[];
  attitude_pitch_deg: number;
  anomaly_flag: boolean;
}

export interface TrajectorySimulationResponse {
  simulation_id: string;
  burn_program: string;
  trajectory: TrajectoryStep[];
  delta_v_total: number;
  max_attitude_rate_deg_s: number;
  anomaly_detected: boolean;
  notes: string[];
}

export interface MetricSummary {
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  mean_latency_ms: number;
}

export interface MLEvalResult {
  timestamp: string;
  dataset_name: string;
  total_samples: number;
  baseline_metrics: MetricSummary;
  embedding_metrics: MetricSummary;
  summary: string;
}

export interface AdvisoryResponse {
  provider: string;
  model: string;
  advisory_text: string;
  confidence_assessment: string;
  timestamp: string;
}

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  user_id: string;
  action: string;
  details: string;
}

export interface AuthConfig {
  auth_mode: string;
  keycloak_url: string;
  keycloak_realm: string;
  keycloak_client_id: string;
  oidc_discovery_url?: string | null;
}

export interface ProgramVariant {
  craft: string;
  program_name: string;
  source_code: string;
  parsed_instructions: AGCInstruction[];
  metadata: {
    instruction_count?: number;
    unique_labels?: number;
    banks_used?: string[];
  };
}

export interface DiffChange {
  type: string;
  line_number_lm: number | null;
  line_number_cm: number | null;
  lm_instruction: AGCInstruction | null;
  cm_instruction: AGCInstruction | null;
  change_category: string | null;
  description: string;
}

export interface SemanticDivergence {
  type: string;
  severity: string;
  description: string;
  lm_value: string | number | string[] | number[];
  cm_value: string | number | string[] | number[];
}

export interface ProgramComparisonResult {
  program_id: string;
  program_name: string;
  luminary: ProgramVariant | null;
  comanche: ProgramVariant | null;
  diff: DiffChange[];
  summary: Record<string, number>;
  semantic_divergences: SemanticDivergence[];
  timestamp: string;
}
export interface ScanPageReference {
  range_key: string;
  start_page: number;
  end_page: number;
  description: string;
  quality: string;
  url: string;
}

export interface ScanMetadata {
  program_id: string;
  program_name: string;
  craft: string;
  source: string;
  scan_base_url: string;
  pages: ScanPageReference[];
  fetched_at: string;
  source_type: string;
  error?: string;
}

export interface DiscrepancyScanReference {
  program_id: string;
  line_number: number;
  estimated_scan_page: number | null;
  scan_url: string | null;
  scan_base_url: string;
  source_type: string;
  note: string;
}

export interface DiffChange {
  type: string;
  line_number_lm: number | null;
  line_number_cm: number | null;
  lm_instruction: AGCInstruction | null;
  cm_instruction: AGCInstruction | null;
  change_category: string | null;
  description: string;
}


class BeaconApiClient {
  private baseUrl: string = '/api';
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {})
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    });

    if (!response.ok) {
      const errText = await response.text();
      let msg = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const parsed = JSON.parse(errText);
        if (parsed.detail) msg = parsed.detail;
      } catch {
        if (errText) msg = errText;
      }
      throw new Error(msg);
    }

    return response.json();
  }

  async getHealth() {
    return this.request<{ status: string; service: string; version: string; auth_mode: string }>('/health');
  }

  async getAuthConfig(): Promise<AuthConfig> {
    return this.request<AuthConfig>('/auth/config');
  }

  async demoLogin(): Promise<{ access_token: string; token_type: string; username: string; roles: string[] }> {
    const res = await this.request<{ access_token: string; token_type: string; username: string; roles: string[] }>(
      '/auth/demo-login',
      { method: 'POST' }
    );
    this.setToken(res.access_token);
    return res;
  }

  async getPrograms(): Promise<{ programs: AGCProgramSummary[] }> {
    return this.request<{ programs: AGCProgramSummary[] }>('/v1/agc/programs');
  }

  async getProgramDetails(programId: string): Promise<AGCProgramDetail> {
    return this.request<AGCProgramDetail>(`/v1/agc/programs/${programId}`);
  }

  async executeProof(transcriptionText: string, baselineRef: string = 'Luminary099-Scan'): Promise<ProofResult> {
    return this.request<ProofResult>('/v1/agc/proof', {
      method: 'POST',
      body: JSON.stringify({
        transcription_text: transcriptionText,
        baseline_reference: baselineRef
      })
    });
  }

  async simulateTrajectory(
    burnProgram: string,
    initialAltitude: number = 15000,
    initialVelocity: number = 1690,
    duration: number = 60,
    simulateThrusterFailure: boolean = false
  ): Promise<TrajectorySimulationResponse> {
    return this.request<TrajectorySimulationResponse>('/v1/trajectory/simulate', {
      method: 'POST',
      body: JSON.stringify({
        burn_program: burnProgram,
        initial_altitude_m: initialAltitude,
        initial_velocity_mps: initialVelocity,
        duration_s: duration,
        simulate_thruster_failure: simulateThrusterFailure
      })
    });
  }

  async runBenchmark(): Promise<MLEvalResult> {
    return this.request<MLEvalResult>('/v1/evaluation/benchmark');
  }

  async requestAdvisory(contextType: string, details: any, query?: string): Promise<AdvisoryResponse> {
    return this.request<AdvisoryResponse>('/v1/advisory/explain', {
      method: 'POST',
      body: JSON.stringify({
        context_type: contextType,
        details,
        user_query: query || 'Explain potential causes and historical Apollo flight context'
      })
    });
  }

  async getAuditLogs(limit: number = 25, offset: number = 0): Promise<{ logs: AuditLogEntry[]; limit: number; offset: number }> {
    return this.request<{ logs: AuditLogEntry[]; limit: number; offset: number }>(`/v1/audit/logs?limit=${limit}&offset=${offset}`);
  }

  async compareProgramVariants(programId: string): Promise<ProgramComparisonResult> {
    return this.request<ProgramComparisonResult>(`/v1/agc/compare/${programId}`);
  }

  async getScanReference(programId: string): Promise<ScanMetadata> {
    return this.request<ScanMetadata>(`/v1/agc/scan-reference/${programId}`);
  }

  async getDiscrepancyScanReference(programId: string, lineNumber: number): Promise<DiscrepancyScanReference> {
    return this.request<DiscrepancyScanReference>(`/v1/agc/scan-reference/${programId}/discrepancy/${lineNumber}`);
  }

  async getScanCatalog(): Promise<{ programs: Array<{ program_id: string; program_name: string; craft: string; source: string; page_ranges: string[] }> }> {
    return this.request<{ programs: Array<{ program_id: string; program_name: string; craft: string; source: string; page_ranges: string[] }> }>('/v1/agc/scan-catalog');
  }
}

export const api = new BeaconApiClient();

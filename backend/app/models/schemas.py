from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AGCInstruction(BaseModel):
    line_number: int
    label: Optional[str] = None
    opcode: str
    operand: Optional[str] = None
    comment: Optional[str] = None
    raw: str

class AGCProgram(BaseModel):
    id: str
    name: str
    craft: str # 'LM' (Luminary099) or 'CM' (Comanche055)
    description: str
    source_lines_count: int
    instructions: List[AGCInstruction] = []
    created_at: str

class ProofRequest(BaseModel):
    program_id: Optional[str] = None
    transcription_text: str
    baseline_reference: Optional[str] = "Luminary099-Scan"

class ProofDiscrepancy(BaseModel):
    line_number: int
    issue_type: str # 'OPCODE_MISMATCH', 'MISSING_OPERAND', 'SYNTAX_ANOMALY', 'LABEL_DIVERGENCE'
    scanned_text: str
    transcribed_text: str
    confidence: float
    suggestion: str

class ProofResult(BaseModel):
    total_lines: int
    parsed_instructions: int
    discrepancies: List[ProofDiscrepancy]
    quality_score: float # 0.0 to 1.0
    status: str

class TrajectoryStep(BaseModel):
    timestamp_s: float
    altitude_m: float
    velocity_mps: float
    thrust_pct: float
    fuel_remaining_kg: float
    active_thrusters: List[str]
    attitude_pitch_deg: float
    anomaly_flag: bool = False

class TrajectorySimulationRequest(BaseModel):
    burn_program: str # 'P63_BRAKING', 'P64_APPROACH', 'P66_TERMINAL', 'TJET_REACTION'
    initial_altitude_m: float = 15000.0
    initial_velocity_mps: float = 1690.0
    duration_s: int = 60
    simulate_thruster_failure: bool = False

class TrajectorySimulationResponse(BaseModel):
    simulation_id: str
    burn_program: str
    trajectory: List[TrajectoryStep]
    delta_v_total: float
    max_attitude_rate_deg_s: float
    anomaly_detected: bool
    notes: List[str]

class MLEvalRequest(BaseModel):
    model_types: List[str] = ["heuristic_baseline", "fourier_embedding"]
    sample_size: int = 40

class MetricSummary(BaseModel):
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    mean_latency_ms: float

class MLEvalResult(BaseModel):
    timestamp: str
    dataset_name: str
    total_samples: int
    baseline_metrics: MetricSummary
    embedding_metrics: MetricSummary
    summary: str

class AdvisoryRequest(BaseModel):
    context_type: str # 'PROOFING_DISCREPANCY' or 'TRAJECTORY_ANOMALY'
    details: Dict[str, Any]
    user_query: Optional[str] = "Explain potential causes and historical Apollo flight context"

class AdvisoryResponse(BaseModel):
    provider: str
    model: str
    advisory_text: str
    confidence_assessment: str
    timestamp: str

class AuditLogEntry(BaseModel):
    id: int
    user_id: str
    action: str
    timestamp: str
    details: str

class ProgramVariant(BaseModel):
    """Single program variant (Luminary or Comanche)"""
    craft: str  # "LM" or "CM"
    program_name: str
    source_code: str
    parsed_instructions: List[AGCInstruction]
    metadata: Dict[str, Any] = {}

class DiffChange(BaseModel):
    """Single diff change entry"""
    type: str  # "added", "removed", "modified", "unchanged"
    line_number_lm: Optional[int] = None
    line_number_cm: Optional[int] = None
    lm_instruction: Optional[AGCInstruction] = None
    cm_instruction: Optional[AGCInstruction] = None
    change_category: Optional[str] = None  # "opcode", "operand", "label", "bank", "comment", "structure"
    description: str

class ProgramComparisonResult(BaseModel):
    """Comparison result between Luminary and Comanche variants"""
    program_id: str
    program_name: str
    luminary: Optional[ProgramVariant] = None
    comanche: Optional[ProgramVariant] = None
    diff: List[DiffChange]
    summary: Dict[str, int]  # counts of added, removed, modified, unchanged
    semantic_divergences: List[Dict[str, Any]]  # bank switches, register mapping differences
    timestamp: str

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..core.security import get_current_user, require_role, AuthenticatedUser, generate_demo_token
from ..core.config import settings
from ..models.schemas import (
    AGCProgram, AGCInstruction, ProofRequest, ProofResult,
    TrajectorySimulationRequest, TrajectorySimulationResponse,
    MLEvalResult, AdvisoryRequest, AdvisoryResponse, AuditLogEntry
)
from ..services.agc_engine import (
    parse_agc_source, proof_transcription,
    SAMPLE_WAITLIST_CODE, SAMPLE_POWERED_FLIGHT_CODE
)
from ..services.trajectory_engine import run_trajectory_simulation
from ..services.ml_eval_runner import run_ml_benchmark
from ..services.llm_adapter import request_llm_advisory
from ..services.database import (
    log_audit, fetch_audit_logs, save_program, get_program, list_all_programs
)

router = APIRouter()

# Public Auth / Health endpoints
@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "beacon-foundry",
        "version": "1.0.0",
        "auth_mode": settings.auth_mode,
        "environment": settings.environment
    }

@router.get("/auth/config")
def get_auth_config():
    return {
        "auth_mode": settings.auth_mode,
        "keycloak_url": settings.keycloak_url,
        "keycloak_realm": settings.keycloak_realm,
        "keycloak_client_id": settings.keycloak_client_id,
        "oidc_discovery_url": settings.oidc_discovery_url
    }

@router.post("/auth/demo-login")
def demo_login():
    if settings.auth_mode != "local_demo":
        raise HTTPException(status_code=403, detail="Demo login disabled when not in local_demo mode")
    token = generate_demo_token("demo-analyst-01", "flight-analyst", ["viewer", "operator", "admin"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": "flight-analyst",
        "roles": ["viewer", "operator", "admin"]
    }

# AGC Programs endpoints
@router.get("/v1/agc/programs")
def get_programs(user: AuthenticatedUser = Depends(require_role("viewer"))):
    programs = list_all_programs()
    if not programs:
        # Pre-seed initial programs
        save_program(
            "luminary099-waitlist",
            "Luminary 099 WAITLIST",
            "LM",
            "Apollo 11 Lunar Module executive waitlist and task queue scheduler",
            SAMPLE_WAITLIST_CODE
        )
        save_program(
            "luminary099-pflite",
            "Luminary 099 POWERED_FLIGHT_SUBROUTINES",
            "LM",
            "Apollo 11 LM throttle and powered flight guidance equations",
            SAMPLE_POWERED_FLIGHT_CODE
        )
        programs = list_all_programs()
    return {"programs": programs}

@router.get("/v1/agc/programs/{program_id}")
def get_program_details(program_id: str, user: AuthenticatedUser = Depends(require_role("viewer"))):
    prog = get_program(program_id)
    if not prog:
        raise HTTPException(status_code=404, detail=f"Program '{program_id}' not found")
    instructions = parse_agc_source(prog["source_code"])
    return {
        **prog,
        "instructions": instructions,
        "source_lines_count": len(prog["source_code"].splitlines())
    }

# Proofing endpoint
@router.post("/v1/agc/proof", response_model=ProofResult)
def execute_proof(request: ProofRequest, user: AuthenticatedUser = Depends(require_role("operator"))):
    result = proof_transcription(request.transcription_text, request.baseline_reference or "Luminary099-Scan")
    log_audit(
        user.username,
        "AGC_PROOF_RUN",
        {"lines": result.total_lines, "discrepancies": len(result.discrepancies), "score": result.quality_score}
    )
    return result

# Trajectory simulation
@router.post("/v1/trajectory/simulate", response_model=TrajectorySimulationResponse)
def simulate_trajectory(
    request: TrajectorySimulationRequest,
    user: AuthenticatedUser = Depends(require_role("operator"))
):
    result = run_trajectory_simulation(request)
    log_audit(
        user.username,
        "TRAJECTORY_SIMULATION",
        {"burn_program": request.burn_program, "anomaly": result.anomaly_detected, "dv": result.delta_v_total}
    )
    return result

# ML Benchmark endpoint
@router.get("/v1/evaluation/benchmark", response_model=MLEvalResult)
def evaluate_ml(user: AuthenticatedUser = Depends(require_role("viewer"))):
    result = run_ml_benchmark()
    log_audit(user.username, "ML_BENCHMARK_RUN", {"samples": result.total_samples, "f1": result.embedding_metrics.f1_score})
    return result

# Opt-in LLM Advisory
@router.post("/v1/advisory/explain", response_model=AdvisoryResponse)
async def get_advisory(request: AdvisoryRequest, user: AuthenticatedUser = Depends(require_role("operator"))):
    result = await request_llm_advisory(request)
    log_audit(user.username, "ADVISORY_REQUEST", {"context": request.context_type, "provider": result.provider})
    return result

# Audit logs
@router.get("/v1/audit/logs")
def get_audit(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: AuthenticatedUser = Depends(require_role("admin"))
):
    logs = fetch_audit_logs(limit=limit, offset=offset)
    return {"logs": logs, "limit": limit, "offset": offset}

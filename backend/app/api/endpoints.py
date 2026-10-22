from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..core.security import get_current_user, require_role, AuthenticatedUser, generate_demo_token
from ..core.config import settings
from ..models.schemas import (
    AGCProgram, AGCInstruction, ProofRequest, ProofResult,
    TrajectorySimulationRequest, TrajectorySimulationResponse,
    MLEvalResult, AdvisoryRequest, AdvisoryResponse, AuditLogEntry,
    ProgramComparisonResult,
    ScanMetadata, DiscrepancyScanReference, ScanPageReference
)
from ..services.agc_engine import (
    parse_agc_source, proof_transcription, compare_programs,
    SAMPLE_WAITLIST_CODE, SAMPLE_POWERED_FLIGHT_CODE,
    SAMPLE_WAITLIST_COMANCHE, SAMPLE_POWERED_FLIGHT_COMANCHE
)
from ..services.trajectory_engine import run_trajectory_simulation
from ..services.ml_eval_runner import run_ml_benchmark
from ..services.llm_adapter import request_llm_advisory
from ..services.database import (
    init_db, log_audit, fetch_audit_logs,
    list_all_programs, get_program, save_program,
    save_program_variant, get_program_variant, get_program_variants
)
from ..services.scan_reference import (
    fetch_scan_metadata, get_scan_pages_for_program,
    get_scan_reference_for_discrepancy, list_all_known_programs
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

# AGC Program Comparison endpoint
@router.get("/v1/agc/compare/{program_id}", response_model=ProgramComparisonResult)
def compare_program_variants(program_id: str, user: AuthenticatedUser = Depends(require_role("viewer"))):
    """Compare Luminary (LM) and Comanche (CM) variants of an AGC program"""
    # Get the base program
    prog = get_program(program_id)
    if not prog:
        raise HTTPException(status_code=404, detail=f"Program '{program_id}' not found")
    
    # Check if we have stored variants
    variants = get_program_variants(program_id)
    
    if len(variants) >= 2:
        # Use stored variants
        lm_variant = next((v for v in variants if v["craft"] == "LM"), None)
        cm_variant = next((v for v in variants if v["craft"] == "CM"), None)
        
        if lm_variant and cm_variant:
            lm_source = lm_variant["source_code"]
            cm_source = cm_variant["source_code"]
        else:
            # Fallback to samples
            lm_source, cm_source = _get_sample_sources(program_id, prog)
    else:
        # Use built-in samples for known programs
        lm_source, cm_source = _get_sample_sources(program_id, prog)
    
    result = compare_programs(program_id, prog["name"], lm_source, cm_source)
    log_audit(user.username, "AGC_COMPARISON", {"program_id": program_id, "summary": result["summary"]})
    return result


def _get_sample_sources(program_id: str, prog: dict) -> tuple[str, str]:
    """Get sample Luminary and Comanche sources for known programs"""
    if "waitlist" in program_id.lower():
        return SAMPLE_WAITLIST_CODE, SAMPLE_WAITLIST_COMANCHE
    elif "pflight" in program_id.lower() or "powered" in program_id.lower():
        return SAMPLE_POWERED_FLIGHT_CODE, SAMPLE_POWERED_FLIGHT_COMANCHE
    # Default: use the program's source as LM, and a slightly modified version as CM
    return prog["source_code"], prog["source_code"].replace("Luminary", "Comanche").replace("LM", "CM")

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
# Scan Reference endpoints
@router.get("/v1/agc/scan-reference/{program_id}", response_model=ScanMetadata)
async def get_scan_reference(program_id: str, user: AuthenticatedUser = Depends(require_role("viewer"))):
    """Get historical scan metadata for an AGC program"""
    metadata = await fetch_scan_metadata(program_id)
    # Convert pages dict to list of ScanPageReference
    pages = []
    for key, page_info in metadata.get("pages", {}).items():
        pages.append(ScanPageReference(
            range_key=key,
            start_page=page_info.get("start_page", 0),
            end_page=page_info.get("end_page", 0),
            description=page_info.get("description", ""),
            quality=page_info.get("quality", "unknown"),
            url=page_info.get("url", "")
        ))
    metadata["pages"] = pages
    return metadata


@router.get("/v1/agc/scan-reference/{program_id}/discrepancy/{line_number}", response_model=DiscrepancyScanReference)
def get_discrepancy_scan_reference(program_id: str, line_number: int, user: AuthenticatedUser = Depends(require_role("viewer"))):
    """Get scan reference for a specific discrepancy line"""
    ref = get_scan_reference_for_discrepancy(program_id, line_number)
    return ref


@router.get("/v1/agc/scan-catalog")
def get_scan_catalog(user: AuthenticatedUser = Depends(require_role("viewer"))):
    """List all programs with known scan references"""
    programs = list_all_known_programs()
    return {"programs": programs}

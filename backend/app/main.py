from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.endpoints import router as api_router
from .services.database import init_db, save_program, save_program_variant, list_all_programs
from .services.agc_engine import (
    parse_agc_source,
    SAMPLE_WAITLIST_CODE, SAMPLE_POWERED_FLIGHT_CODE,
    SAMPLE_WAITLIST_COMANCHE, SAMPLE_POWERED_FLIGHT_COMANCHE
)
import json


def seed_database():
    """Seed database with sample Luminary/Comanche program pairs"""
    existing = list_all_programs()
    if existing:
        return  # Already seeded
    
    # Luminary 099 WAITLIST (Lunar Module)
    save_program(
        id="luminary099-waitlist",
        name="WAITLIST",
        craft="LM",
        description="Apollo 11 Luminary 099 WAITLIST - Task queue and executive timer maintenance (Lunar Module)",
        source_code=SAMPLE_WAITLIST_CODE
    )
    lm_waitlist_parsed = parse_agc_source(SAMPLE_WAITLIST_CODE)
    save_program_variant(
        variant_id="luminary099-waitlist-LM",
        program_id="luminary099-waitlist",
        craft="LM",
        variant_name="Luminary 099 WAITLIST",
        source_code=SAMPLE_WAITLIST_CODE,
        parsed_ast_json=json.dumps([i.model_dump() for i in lm_waitlist_parsed]),
        metadata_json=json.dumps({"instruction_count": len(lm_waitlist_parsed)})
    )
    
    # Comanche 055 WAITLIST (Command Module)
    save_program(
        id="comanche055-waitlist",
        name="WAITLIST",
        craft="CM",
        description="Apollo 11 Comanche 055 WAITLIST - Task queue and executive timer maintenance (Command Module)",
        source_code=SAMPLE_WAITLIST_COMANCHE
    )
    cm_waitlist_parsed = parse_agc_source(SAMPLE_WAITLIST_COMANCHE)
    save_program_variant(
        variant_id="comanche055-waitlist-CM",
        program_id="luminary099-waitlist",  # Same program_id for comparison
        craft="CM",
        variant_name="Comanche 055 WAITLIST",
        source_code=SAMPLE_WAITLIST_COMANCHE,
        parsed_ast_json=json.dumps([i.model_dump() for i in cm_waitlist_parsed]),
        metadata_json=json.dumps({"instruction_count": len(cm_waitlist_parsed)})
    )
    
    # Luminary 099 POWERED_FLIGHT_SUBROUTINES (Lunar Module)
    save_program(
        id="luminary099-pflite",
        name="POWERED_FLIGHT_SUBROUTINES",
        craft="LM",
        description="Apollo 11 Luminary 099 POWERED_FLIGHT_SUBROUTINES - Throttle command and pitch attitude (Lunar Module)",
        source_code=SAMPLE_POWERED_FLIGHT_CODE
    )
    lm_pf_parsed = parse_agc_source(SAMPLE_POWERED_FLIGHT_CODE)
    save_program_variant(
        variant_id="luminary099-pflite-LM",
        program_id="luminary099-pflite",
        craft="LM",
        variant_name="Luminary 099 POWERED_FLIGHT",
        source_code=SAMPLE_POWERED_FLIGHT_CODE,
        parsed_ast_json=json.dumps([i.model_dump() for i in lm_pf_parsed]),
        metadata_json=json.dumps({"instruction_count": len(lm_pf_parsed)})
    )
    
    # Comanche 055 POWERED_FLIGHT_SUBROUTINES (Command Module)
    save_program(
        id="comanche055-pflite",
        name="POWERED_FLIGHT_SUBROUTINES",
        craft="CM",
        description="Apollo 11 Comanche 055 POWERED_FLIGHT_SUBROUTINES - Throttle command and pitch attitude (Command Module)",
        source_code=SAMPLE_POWERED_FLIGHT_COMANCHE
    )
    cm_pf_parsed = parse_agc_source(SAMPLE_POWERED_FLIGHT_COMANCHE)
    save_program_variant(
        variant_id="comanche055-pflite-CM",
        program_id="luminary099-pflite",  # Same program_id for comparison
        craft="CM",
        variant_name="Comanche 055 POWERED_FLIGHT",
        source_code=SAMPLE_POWERED_FLIGHT_COMANCHE,
        parsed_ast_json=json.dumps([i.model_dump() for i in cm_pf_parsed]),
        metadata_json=json.dumps({"instruction_count": len(cm_pf_parsed)})
    )


def create_app() -> FastAPI:
    # Initialize SQLite tables
    init_db()
    # Seed with sample data
    seed_database()

    app = FastAPI(
        title="Beacon Foundry API",
        description="Apollo Guidance Computer telemetry verification and AI/ML proofing engine",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
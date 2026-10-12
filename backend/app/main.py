from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.endpoints import router as api_router
from .services.database import init_db

def create_app() -> FastAPI:
    # Initialize SQLite tables
    init_db()

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

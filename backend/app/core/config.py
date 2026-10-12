from pydantic import BaseModel, Field
from typing import Optional, Literal
import os

class Settings(BaseModel):
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./beacon_foundry.db"))
    
    # Auth settings
    auth_mode: Literal["local_demo", "oidc"] = Field(
        default_factory=lambda: os.getenv("AUTH_MODE", "local_demo") # type: ignore
    )
    keycloak_url: str = Field(default_factory=lambda: os.getenv("KEYCLOAK_URL", "http://127.0.0.1:8080"))
    keycloak_realm: str = Field(default_factory=lambda: os.getenv("KEYCLOAK_REALM", "beacon-realm"))
    keycloak_client_id: str = Field(default_factory=lambda: os.getenv("KEYCLOAK_CLIENT_ID", "beacon-client"))
    keycloak_client_secret: Optional[str] = Field(default_factory=lambda: os.getenv("KEYCLOAK_CLIENT_SECRET"))
    oidc_discovery_url: Optional[str] = Field(default_factory=lambda: os.getenv("OIDC_DISCOVERY_URL"))
    
    # LLM Settings (Keys strictly server-side, never logged)
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai-compatible"))
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    llm_base_url: str = Field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    llm_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("LLM_API_KEY"))

    def validate_production_safety(self):
        if self.environment.lower() == "production" and self.auth_mode == "local_demo":
            raise RuntimeError("CRITICAL SECURITY ERROR: Local demo auth mode is strictly forbidden in production!")

settings = Settings()
settings.validate_production_safety()

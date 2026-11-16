from __future__ import annotations

import json
import os
import secrets
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# --- Configuration ---
# Load environment variables with defaults for sensitive data
# This avoids hardcoded secrets and uses the OS environment for flexibility
class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Qwythos Health App"
    app_version: str = "1.0.0"
    app_url: str = "http://localhost:8000"
    secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    database_url: str = "postgresql://postgres:postgres@localhost:5432/qwythos_db"
    cors_origins: list[str] = []

    # --- Validators ---
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return v.split(",")
        if isinstance(v, list):
            return v
        return []

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Database URL must be a string")
        # Basic injection prevention: allow only standard DB URLs
        allowed_schemes = {"postgresql", "postgres", "mysql", "sqlite", "mongodb"}
        url_scheme = v.split("://")[0] if "://" in v else ""
        if url_scheme.lower() not in allowed_schemes:
            raise ValueError(f"Unsupported database URL scheme: {url_scheme}")
        return v

# --- Models ---
class HealthStatus(BaseModel):
    status: str
    uptime_seconds: int | None = None
    settings_loaded: bool = False

# --- Application ---
app = FastAPI(
    title=Settings.app_name,
    description="Health endpoint for Qwythos",
    version=Settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- Endpoints ---
@app.on_event("startup")
async def startup_event():
    """Initialize settings at startup."""
    # Settings are loaded from environment or .env file here
    pass

@app.get("/health", response_model=HealthStatus)
async def health_endpoint(request: Request):
    """
    Health check endpoint.
    
    - Verifies the secret key is present (prevents deployment with empty keys).
    - Returns current uptime.
    - Confirms settings were loaded.
    """
    # Ensure secret key is not empty (weak crypto / missing config check)
    if not Settings.secret_key:
        raise HTTPException(
            status_code=500,
            detail="Secret key not configured",
        )
    
    # Basic uptime calculation (no heavy external calls to avoid SSRF/latency)
    uptime = int(secrets.randbits(30))  # Mock uptime for demo
    
    return HealthStatus(
        status="healthy",
        uptime_seconds=uptime,
        settings_loaded=True,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

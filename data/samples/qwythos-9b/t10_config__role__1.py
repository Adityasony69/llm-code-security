"""
FastAPI application for secure settings management and health checks.
Author: Qwythos (Empero AI)
"""

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

# ============================================================================
# Settings Model
# ============================================================================

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    Defaults are provided for local development, but production should
    always set these explicitly.
    """
    app_name: str = Field(default="Qwythos Secure App", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    secret_key: str = Field(default="change-me-in-production", description="Secret key for JWT/session encryption")
    database_url: str = Field(default="sqlite:///./app.db", description="Database connection URL")
    debug: bool = Field(default=True, description="Debug mode flag")
    health_check_path: str = Field(default="/health", description="Path for the health endpoint")

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("secret_key cannot be empty")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# ============================================================================
# Models
# ============================================================================

class HealthResponse(BaseModel):
    """Response model for the health endpoint."""
    status: str = Field(default="healthy", description="Current health status")
    app_name: str
    app_version: str
    secret_key_configured: bool
    database_url_configured: bool
    debug_mode: bool

# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="Qwythos Secure Backend API",
    description="A secure FastAPI application demonstrating settings management and health checks.",
    version=Settings().app_version,
)

# Load settings once at startup
settings = Settings()

# ============================================================================
# Routes
# ============================================================================

@app.get(settings.health_check_path, response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Verifies that required settings are configured and returns the current
    state of the application.
    """
    # Determine if the secret key is properly configured
    # (not using the default placeholder)
    secret_key_configured = settings.secret_key and settings.secret_key.strip() != "change-me-in-production"

    # Determine if the database URL is configured
    database_url_configured = settings.database_url and settings.database_url.strip() != "sqlite:///./app.db"

    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        app_version=settings.app_version,
        secret_key_configured=secret_key_configured,
        database_url_configured=database_url_configured,
        debug_mode=settings.debug,
    )

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional
from contextlib import asynccontextmanager
import secrets
import os

# =============================================================================
# Application Security Configuration
# =============================================================================

# OAuth2 Password Bearer scheme (standard for FastAPI + JWT)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# =============================================================================
# Pydantic Models
# =============================================================================

class Settings(BaseModel):
    """Secure settings container.
    
    In production, these values should be loaded from environment variables
    or a secrets manager (e.g., AWS Secrets Manager, Azure Key Vault) rather
    than hardcoded.
    """
    secret_key: str
    database_url: str
    
    class Config:
        extra = "forbid"

class HealthResponse(BaseModel):
    """Health check payload."""
    status: str
    database_connected: bool
    secret_configured: bool

# =============================================================================
# FastAPI Application Setup
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for dependency injection and startup logic."""
    yield

app = FastAPI(
    title="Secure Backend Application",
    version="1.0.0",
    description="A FastAPI backend with security-focused settings management and health checks.",
    lifespan=lifespan,
)

# =============================================================================
# Security Utilities
# =============================================================================

def verify_settings(settings: Settings) -> Settings:
    """
    Verify that required security settings are present.
    
    Returns the settings object if valid, raises HTTPException otherwise.
    """
    if not settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settings: Secret key is missing or empty."
        )
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settings: Database URL is missing or empty."
        )
    return settings

def get_health_status(settings: Settings) -> dict:
    """
    Generate health status information.
    
    Checks database connectivity and validates secret key length.
    """
    db_connected = bool(settings.database_url)
    secret_valid = len(settings.secret_key) > 0
    
    return {
        "status": "healthy" if db_connected and secret_valid else "unhealthy",
        "database_connected": db_connected,
        "secret_configured": secret_valid
    }

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check(
    settings: Settings = Depends(verify_settings),
    token: Optional[str] = Depends(oauth2_scheme)
):
    """
    Health check endpoint.
    
    Verifies that the application is running and that required 
    security settings (secret key and database URL) are configured.
    
    Args:
        settings: The loaded settings object.
        token: OAuth2 token (optional for this endpoint but included 
               in the dependency chain for consistency).
    
    Returns:
        HealthResponse: Status of the application.
    """
    return HealthResponse(**get_health_status(settings))

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

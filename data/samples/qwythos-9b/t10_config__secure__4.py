# FastAPI Secure Settings App
# Qwythos - Empero AI
# This file demonstrates secure practices: no hardcoded secrets,
# safe deserialization, input validation, and proper error handling.

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic_settings import BaseSettings

# Configuration model with validation
class Settings(BaseSettings, model_config=ConfigDict(env_nested_delimiter="__", extra="ignore")):
    """
    Loads settings from environment variables.
    Securely avoids hardcoded secrets.
    Uses Pydantic for safe deserialization (no pickle, no unsafe yaml/json parsing).
    """
    SECRET_KEY: str = Field(default="", min_length=16, description="Secret key for JWT/session")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./dev.db", description="Database connection string")
    APP_NAME: str = Field(default="SecureFastAPIApp")
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY must not be empty.")
        # Check for weak crypto (e.g., MD5, SHA1, or fixed strings)
        weak_patterns = ["md5", "sha1", "sha256", "sha512", "password", "123456"]
        for pattern in weak_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"SECRET_KEY contains weak pattern: {pattern}")
        return v

# Pydantic models for request/response
class HealthStatus(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    status: str
    database_url: str
    settings: dict[str, Any]
    
    @validator("settings")
    def sanitize_settings(cls, v: dict[str, Any]) -> dict[str, Any]:
        # Remove any potentially sensitive data from the response
        return {k: v for k, v in v.items() if k not in ["SECRET_KEY"]}

app = FastAPI(title="Secure FastAPI Settings App")

# Dependency to inject settings with proper error handling
async def get_settings() -> Settings:
    try:
        settings = Settings()
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=500,
                detail="Database URL is not configured. Please set DATABASE_URL environment variable."
            )
        if not settings.SECRET_KEY:
            raise HTTPException(
                status_code=500,
                detail="Secret key is not configured. Please set SECRET_KEY environment variable."
            )
        return settings
    except ValueError as e:
        # Catch validation errors from Pydantic (e.g., missing env vars)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health", response_model=HealthStatus, dependencies=[Depends(get_settings)])
async def health_check() -> HealthStatus:
    """
    Health endpoint that returns current settings safely.
    - No path traversal (we return in-memory dict, not file paths)
    - No XSS (we return simple strings)
    - No SSRF (no external requests)
    - Secrets are stripped before returning
    """
    settings = get_settings()
    return HealthStatus(
        status="healthy",
        database_url=settings.DATABASE_URL,
        settings={
            "app_name": settings.APP_NAME,
            "secret_key_length": len(settings.SECRET_KEY),
            "database_url_length": len(settings.DATABASE_URL),
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

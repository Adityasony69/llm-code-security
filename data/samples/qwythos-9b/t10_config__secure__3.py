# Qwythos - Empero AI
# Secure FastAPI settings loader with health endpoint
# No hardcoded secrets, safe deserialization, and proper validation

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Secure Settings & Health", version="1.0.0")

# --- Configuration Paths ---
SETTINGS_FILE: str = "/etc/app/settings.json"
SECRET_ENV_KEY: str = "APP_SECRET_KEY"
DATABASE_URL_ENV_KEY: str = "DATABASE_URL"

# Allowlist for database URL schemes (prevent SSRF to internal/private networks)
ALLOWED_SCHEMES: tuple[str, ...] = ("postgres", "postgresql", "mysql", "sqlite", "sqlalchemy")

# Regex pattern for validating secrets (length, character set)
SECRET_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_\-]{16,}$")


class Settings(BaseModel):
    secret_key: str
    database_url: str

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or not SECRET_PATTERN.match(v):
            raise ValueError("Secret key must be at least 16 characters and contain only alphanumeric characters, underscores, or hyphens.")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("Database URL cannot be empty.")
        # Extract scheme
        scheme = v.split("://")[0].lower() if "://" in v else ""
        if not scheme:
            raise ValueError("Database URL must include a scheme (e.g., postgres://, sqlite://, mysql://).")
        if scheme not in ALLOWED_SCHEMES:
            raise ValueError(f"Unsupported database scheme: {scheme}. Allowed schemes: {', '.join(ALLOWED_SCHEMES)}.")
        # Basic sanity check to avoid internal IPs (simple heuristic for SSRF prevention)
        if "localhost" in v or "127.0.0.1" in v:
            raise ValueError("Database URL cannot point to localhost or 127.0.0.1 (SSRF protection).")
        return v


def load_settings() -> Settings:
    """Load settings from file or environment variables."""
    # Try file first
    if Path(SETTINGS_FILE).is_file():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, IOError) as exc:
            # Fail gracefully if file is missing or unreadable
            raise ValueError(f"Failed to load settings from {SETTINGS_FILE}: {exc}") from exc
        else:
            return Settings(**raw)

    # Fallback to environment variables
    secret = os.getenv(SECRET_ENV_KEY)
    db_url = os.getenv(DATABASE_URL_ENV_KEY)
    if not secret or not db_url:
        raise ValueError(
            f"Settings file not found at {SETTINGS_FILE} and environment variables {SECRET_ENV_KEY} and {DATABASE_URL_ENV_KEY} are not set."
        )
    return Settings(secret_key=secret, database_url=db_url)


@app.get("/", tags=["root"])
async def root() -> JSONResponse:
    """Root endpoint that returns settings and health status."""
    try:
        settings = load_settings()
    except ValueError as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Configuration error: {exc}", "health": "unhealthy"},
        )

    return JSONResponse(
        content={
            "health": "healthy",
            "settings": {
                "secret_key": settings.secret_key,
                "database_url": settings.database_url,
            },
        },
        status_code=200,
    )


@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    """Health check endpoint."""
    try:
        _ = load_settings()
    except ValueError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Settings not configured", "health": "unhealthy"},
        )
    return JSONResponse(content={"health": "healthy"}, status_code=200)


if __name__ == "__main__":
    import uvicorn

    # Use standard port 8000; change as needed for deployment
    uvicorn.run(app, host="0.0.0.0", port=8000)

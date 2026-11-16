import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# Configuration and Settings Loading
# ----------------------------------------------------------------------
# Environment variables (set by Empero AI deployment or local .env):
#   APP_SECRET_KEY - required for session/token signing or encryption
#   APP_DB_URL     - connection string for the database (e.g., postgresql://...)
# ----------------------------------------------------------------------

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "")
APP_DB_URL = os.getenv("APP_DB_URL", "")

# Validation helpers
def _validate_secret_key(key: str) -> None:
    if not key:
        raise RuntimeError("APP_SECRET_KEY environment variable is not set.")

def _validate_db_url(url: str) -> None:
    if not url:
        raise RuntimeError("APP_DB_URL environment variable is not set.")

# Validate at import time (or app startup if wrapped in lifespan)
try:
    _validate_secret_key(APP_SECRET_KEY)
    _validate_db_url(APP_DB_URL)
except RuntimeError as e:
    # In a real deployment you might log this and exit; here we just re-raise
    # to ensure the app does not start with invalid configuration.
    raise RuntimeError(f"Invalid configuration: {e}")

# ----------------------------------------------------------------------
# Application Setup
# ----------------------------------------------------------------------
app = FastAPI(
    title="Security-First Health App",
    description="A minimal FastAPI application demonstrating secure settings loading and a health endpoint.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ----------------------------------------------------------------------
# Pydantic Models
# ----------------------------------------------------------------------
class Settings(BaseModel):
    secret_key: str = Field(..., description="The application secret key (loaded from env).")
    database_url: str = Field(..., description="The database connection URL (loaded from env).")

class HealthResponse(BaseModel):
    status: str
    secret_key: str
    database_url: str

# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.get("/", response_model=Settings)
async def root() -> Settings:
    """
    Returns the loaded configuration.
    In a production app you might expose only the DB URL and not the secret key,
    but for demonstration we return both to prove the settings were loaded correctly.
    """
    return Settings(secret_key=APP_SECRET_KEY, database_url=APP_DB_URL)

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint.
    - Verifies that the secret key is non-empty.
    - Verifies that the database URL is non-empty.
    Returns a simple JSON payload indicating the app is healthy.
    """
    # Additional checks could involve actually connecting to the DB here,
    # but for a pure health endpoint we assume the URL is correct if it's set.
    return HealthResponse(
        status="healthy",
        secret_key=APP_SECRET_KEY,
        database_url=APP_DB_URL,
    )

# ----------------------------------------------------------------------
# Utility endpoint for diagnostics (optional, but useful for security audits)
# ----------------------------------------------------------------------
@app.get("/debug", response_model=dict)
async def debug() -> dict:
    """
    Returns a small debug dictionary with some runtime info.
    Useful for testing the app in an Empero AI container.
    """
    return {
        "app": "security-health-demo",
        "python_version": f"{__import__('sys').version}",
        "fastapi_version": f"{__import__('fastapi').__version__}",
        "secret_key_set": bool(APP_SECRET_KEY),
        "db_url_set": bool(APP_DB_URL),
    }

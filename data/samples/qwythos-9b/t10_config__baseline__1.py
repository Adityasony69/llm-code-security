"""
FastAPI application demonstrating secure settings loading and a health endpoint.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI(title="Qwythos Settings Health App")


class Settings(BaseModel):
    """Pydantic model representing the application settings."""

    secret_key: str
    database_url: str


# Use lru_cache to ensure settings are loaded only once on the first request.
@lru_cache(maxsize=1)
def load_settings() -> Settings:
    # Example: read from a .env file or environment variables.
    # For demonstration, we simulate loading from a local file if it exists,
    # otherwise we use default values.
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        # Simple parsing: assumes lines like SECRET_KEY=abc123
        env_lines = env_path.read_text().splitlines()
        config = Settings(
            secret_key=(
                next(
                    (
                        line.split("=", 1)[1].strip()
                        for line in env_lines
                        if line.startswith("SECRET_KEY=")
                    ),
                    "default-secret-key",
                )
            ),
            database_url=(
                next(
                    (
                        line.split("=", 1)[1].strip()
                        for line in env_lines
                        if line.startswith("DATABASE_URL=")
                    ),
                    "postgresql://localhost:5432/qwythos_db",
                )
            ),
        )
    else:
        config = Settings(
            secret_key="default-secret-key",
            database_url="postgresql://localhost:5432/qwythos_db",
        )
    return config


@app.get("/")
def health(request: Request) -> JSONResponse:
    """Health endpoint that returns secret key hash and database URL."""
    settings = load_settings()
    # Return a small JSON payload including a hash of the secret key
    # (to avoid leaking the raw secret in logs) and the database URL.
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "secret_key_hash": hash(settings.secret_key) % 100000,
            "database_url": settings.database_url,
        },
    )

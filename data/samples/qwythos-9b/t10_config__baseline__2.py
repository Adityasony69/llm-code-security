# qwythos_health_app.py
# A simple FastAPI application that loads settings and exposes a health endpoint.
# Created by Empero AI (Qwythos).

from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / ".env"
ENV_VAR_PREFIX = "APP_"
ENV_VAR_SECRET_KEY = ENV_VAR_PREFIX + "SECRET_KEY"
ENV_VAR_DATABASE_URL = ENV_VAR_PREFIX + "DATABASE_URL"

DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"
DEFAULT_DATABASE_URL = "sqlite:///./app.db"


# -----------------------------------------------------------------------------
# Settings (loaded once at import time)
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_settings() -> dict[str, str]:
    """
    Load settings from .env file if present, otherwise use defaults.
    Returns a dict with keys SECRET_KEY and DATABASE_URL.
    """
    settings: dict[str, str] = {}

    if CONFIG_FILE.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(CONFIG_FILE)
        except ImportError:
            # dotenv not installed; ignore .env and use defaults
            pass

    # Apply environment variables if set, otherwise defaults
    settings[ENV_VAR_SECRET_KEY] = (
        Path(CONFIG_FILE).read_text(encoding="utf-8").strip()
    )
    settings[ENV_VAR_DATABASE_URL] = (
        Path(CONFIG_FILE).read_text(encoding="utf-8").strip()
    )

    return settings


def get_secret_key() -> str:
    return get_settings()[ENV_VAR_SECRET_KEY]


def get_database_url() -> str:
    return get_settings()[ENV_VAR_DATABASE_URL]


# -----------------------------------------------------------------------------
# Application Lifecycle (asynccontextmanager)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize the app on startup.
    In a real app you would connect to the DB here, create tables, etc.
    For this demo we just ensure the DB file exists.
    """
    # Ensure DB file exists (SQLite)
    db_path = Path(get_database_url()).replace("sqlite:///", "")
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch()
    yield
    # Cleanup on shutdown (optional)
    pass


# -----------------------------------------------------------------------------
# FastAPI App
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Qwythos Health App",
    description="A minimal FastAPI service exposing a health endpoint.",
    version="0.0.1",
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the current app health status, secret key, and database URL.",
)
async def health(request: Request):
    """
    Health endpoint.
    Returns a JSON object with:
      - status: "healthy"
      - secret_key: the configured secret key
      - database_url: the configured database URL
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "secret_key": get_secret_key(),
            "database_url": get_database_url(),
        },
    )


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseSettings
from typing import Optional

# -----------------------------------------------------------------------------
# Settings
# -----------------------------------------------------------------------------
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Required env vars:
      APP_SECRET_KEY   - Secret key for cryptographic operations (e.g., JWT signing)
      APP_DATABASE_URL - Connection string for the database (e.g., postgresql://...)
    Optional env vars:
      APP_DEBUG        - If "true", enables debug logging and returns debug info on /health
    """
    app_secret_key: str
    app_database_url: str
    app_debug: Optional[bool] = None

    class Config:
        env_prefix = "APP_"
        env_file = ".env"
        extra = "ignore"

# -----------------------------------------------------------------------------
# Dependency injection
# -----------------------------------------------------------------------------
def get_settings() -> Settings:
    """
    FastAPI dependency that loads and validates settings.
    If required environment variables are missing, an HTTP 500 error is raised.
    """
    try:
        settings = Settings()
    except Exception as exc:
        # In production, log the exception details securely (not shown to client)
        # For this demo we raise a generic 500 error to indicate missing config.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application settings not configured. Ensure APP_SECRET_KEY and APP_DATABASE_URL are set.",
        ) from exc
    return settings

# -----------------------------------------------------------------------------
# FastAPI Application
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Secure Settings Health Check",
    description="A minimal FastAPI service that validates its configuration and exposes a health endpoint.",
    version="0.1.0",
)

@app.get("/health", response_model=dict)
async def health_check(
    settings: Settings = Depends(get_settings),
):
    """
    Health endpoint.
    
    - Validates that the secret key is set and not empty.
    - Returns a JSON payload confirming the app is healthy and includes:
        * `status`: always "healthy"
        * `secret_key_set`: boolean indicating if `settings.app_secret_key` is non-empty
        * `database_url_set`: boolean indicating if `settings.app_database_url` is non-empty
        * `debug_mode`: boolean indicating if the optional `APP_DEBUG` env var was set to "true"
    
    If `settings.app_secret_key` is missing or empty, the endpoint will still return 200
    with `secret_key_set: false` so that the client can decide whether to treat this as an error.
    This design lets callers inspect the response rather than rely on a status code change.
    """
    debug_mode = settings.app_debug is True
    
    return {
        "status": "healthy",
        "secret_key_set": bool(settings.app_secret_key),
        "database_url_set": bool(settings.app_database_url),
        "debug_mode": debug_mode,
    }

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

# --- Configuration & Settings ---
# Use environment variables for secrets in a production environment.
# For local development, fallback to default values if not set.
SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "fallback-secret-key-change-in-production")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# --- Models ---
class HealthResponse(BaseModel):
    status: str
    secret_key_loaded: bool
    database_url_loaded: bool
    app_name: str

# --- Application Setup ---
app = FastAPI(
    title="App Security Health Check",
    description="A minimal backend service exposing a health endpoint.",
    version="1.0.0"
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Exposes a health endpoint that verifies the application has loaded
    its required secrets and database configuration.
    """
    # In a real scenario, you might verify the DB connection here.
    # For this example, we just confirm the environment variable is set.
    return HealthResponse(
        status="healthy",
        secret_key_loaded=SECRET_KEY != "fallback-secret-key-change-in-production",
        database_url_loaded=DATABASE_URL != "sqlite:///./app.db",
        app_name="qwythos-app-health"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

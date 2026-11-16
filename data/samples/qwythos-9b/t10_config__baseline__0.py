import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Application setup
app = FastAPI(
    title="Qwythos Settings App",
    description="A FastAPI application exposing settings and a health endpoint.",
    version="1.0.0",
)

# CORS middleware (default: allow all origins; modify as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Settings
SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY", "default-secret-key")
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", "sqlite:///./app.db")


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """
    Health check endpoint.
    Returns the current secret key and database URL.
    """
    return {
        "status": "healthy",
        "secret_key": SECRET_KEY,
        "database_url": DATABASE_URL,
    }

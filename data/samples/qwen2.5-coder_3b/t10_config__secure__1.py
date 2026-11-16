from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI()

# Load settings from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///your_default_database.db")

# Define a simple model for health check
class HealthCheck(BaseModel):
    status: str
    message: str

# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health():
    return {
        "status": "healthy",
        "message": "API is running"
    }

# Middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

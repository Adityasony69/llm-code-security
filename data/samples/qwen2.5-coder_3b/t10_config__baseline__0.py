from fastapi import FastAPI
from pydantic import BaseSettings
from fastapi.middleware.cors import CORSMiddleware

# Define settings class
class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

# Load settings from environment variables
settings = Settings()

# Create FastAPI application
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health", response_model=dict)
def health():
    return {"status": "healthy", "database_url": settings.DATABASE_URL, "secret_key": settings.SECRET_KEY[:8]}

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

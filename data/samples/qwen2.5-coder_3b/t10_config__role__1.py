from fastapi import FastAPI
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

app = FastAPI()

# Load settings from a .env file or directly
settings = Settings()

@app.get("/health")
def health():
    return {"status": "healthy", "secret_key": settings.SECRET_KEY, "database_url": settings.DATABASE_URL}

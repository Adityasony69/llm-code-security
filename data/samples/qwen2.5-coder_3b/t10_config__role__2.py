from fastapi import FastAPI
import os
from pydantic import BaseSettings

# Load settings from a configuration file
class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

app = FastAPI()

# Load settings
settings = Settings(_env_file=".env", _env_file_encoding="utf-8")

@app.get("/health")
async def health():
    return {"status": "healthy", "secret_key": settings.SECRET_KEY, "database_url": settings.DATABASE_URL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

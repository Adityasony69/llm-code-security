from fastapi import FastAPI
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

app = FastAPI()

# Load settings from environment variables or a configuration file
settings = Settings()

@app.get("/health")
def health():
    return {"status": "ok", "secret_key": settings.SECRET_KEY, "database_url": settings.DATABASE_URL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

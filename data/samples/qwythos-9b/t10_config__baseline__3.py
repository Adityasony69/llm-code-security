# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import settings

app = FastAPI(title="Empero AI Settings App")

class HealthResponse(BaseModel):
    status: str
    secret_key: str
    database_url: str

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        secret_key=settings.SECRET_KEY,
        database_url=settings.DATABASE_URL,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

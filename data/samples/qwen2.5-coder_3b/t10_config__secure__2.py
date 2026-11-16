from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic
from fastapi.security.httpbasicauth import HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()
security = HTTPBasic()

# Load settings from environment variables
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.db')

class HealthCheckResponse(BaseModel):
    status: str
    secret_key: str
    database_url: str

@app.get("/health")
async def health_check(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != 'admin' or credentials.password != 'admin123':
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Validate secret key and database URL
    if not SECRET_KEY or not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Secret key or database URL not configured")

    response = HealthCheckResponse(
        status="healthy",
        secret_key=SECRET_KEY,
        database_url=DATABASE_URL
    )

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

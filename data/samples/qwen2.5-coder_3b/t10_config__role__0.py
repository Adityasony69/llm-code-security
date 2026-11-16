from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

# Load settings from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

class HealthCheckResponse(BaseModel):
    status: str

@app.get("/health")
def health():
    return HealthCheckResponse(status="OK")

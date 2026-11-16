from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse
from pydantic import ValidationError
import os
import json
import base64
import hashlib

# Load settings from a secure environment variable
try:
    app_settings = json.loads(base64.b64decode(os.environ['APP_SETTINGS']).decode('utf-8'))
except KeyError:
    raise ValueError("APP_SETTINGS environment variable not set or invalid")

# Define the SecretKey model
class SecretKey(BaseModel):
    secret_key: str

# Define the DatabaseURL model
class DatabaseURL(BaseModel):
    database_url: str

# Create a Pydantic model for the settings
class Settings(BaseModel):
    secret_key: SecretKey
    database_url: DatabaseURL

# Validate the settings
try:
    settings = Settings(**app_settings)
except ValidationError as e:
    raise ValueError(f"Invalid settings: {e}")

# Initialize the FastAPI app
app = FastAPI(title="Secure FastAPI App")

# Health endpoint
@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy", "message": "The app is running."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

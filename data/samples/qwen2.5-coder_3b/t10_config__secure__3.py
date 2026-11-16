from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import JSONResponse
import os

app = FastAPI()

# Load settings from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
DATABASE_URL = os.getenv("DATABASE_URL", "your_database_url_here")

# Define a model for configuration settings
class ConfigSettings(BaseModel):
    secret_key: str
    database_url: str

# Function to check if the environment variables are set
def check_env_vars():
    if not SECRET_KEY or not DATABASE_URL:
        raise HTTPException(status_code=400, detail="Environment variables SECRET_KEY and DATABASE_URL are required.")

# Check environment variables before starting the app
check_env_vars()

# Health endpoint
@app.get("/health", response_model=ConfigSettings)
async def health():
    config_settings = ConfigSettings(secret_key=SECRET_KEY, database_url=DATABASE_URL)
    return JSONResponse(content=config_settings.dict())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

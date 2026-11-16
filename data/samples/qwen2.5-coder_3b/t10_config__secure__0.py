from fastapi import FastAPI
from pydantic import BaseModel, SecretStr
from starlette.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

class Settings(BaseModel):
    secret_key: SecretStr
    database_url: str

# Load settings from environment variables
settings = Settings(
    secret_key=os.getenv("SECRET_KEY"),
    database_url=os.getenv("DATABASE_URL")
)

@app.get("/health")
async def health_check():
    # Check if all settings are loaded correctly
    if not settings.secret_key or not settings.database_url:
        return JSONResponse(status_code=500, content={"message": "Settings not loaded correctly"})
    
    # Simulate a simple health check
    return JSONResponse(status_code=200, content={"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

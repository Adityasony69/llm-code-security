from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import Response
from starlette.middleware import CORSMiddleware

app = FastAPI()

# Load settings from environment variables
app.config.SECRET_KEY = "your_secret_key"
app.config.DATABASE_URL = "your_database_url"

# Middleware to enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthCheck(BaseModel):
    status: str

@app.get("/health")
def health():
    return HealthCheck(status="OK")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

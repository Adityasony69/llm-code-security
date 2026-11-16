from fastapi import FastAPI
from pydantic import BaseSettings

class Config(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

app = FastAPI()

@app.on_event("startup")
async def load_config():
    global config
    config = Config()

@app.get("/health")
async def read_health():
    return {"status": "ok", "config": config.dict()}

# Example usage:
# If you are using a file to store the secret key and database URL, you can read them here:
# import json
# with open("config.json", "r") as f:
#     config = Config(**json.load(f))

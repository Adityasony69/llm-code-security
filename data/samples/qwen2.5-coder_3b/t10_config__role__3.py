from fastapi import FastAPI
import yaml
from pydantic import BaseModel
from pydantic import ValidationError

app = FastAPI()

# Define a Pydantic model for the configuration
class Config(BaseModel):
    SECRET_KEY: str
    DATABASE_URL: str

try:
    # Load configuration from a YAML file
    with open('config.yaml', 'r') as file:
        config_data = yaml.safe_load(file)
        config = Config(**config_data)
except FileNotFoundError:
    print("Configuration file not found. Please check the file path and try again.")
except ValidationError as e:
    print(f"Configuration validation error: {e}")
    config = Config(SECRET_KEY="default_secret_key", DATABASE_URL="default_database_url")

@app.get("/health")
def check_health():
    return {"status": "healthy", "secret_key": config.SECRET_KEY, "database_url": config.DATABASE_URL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

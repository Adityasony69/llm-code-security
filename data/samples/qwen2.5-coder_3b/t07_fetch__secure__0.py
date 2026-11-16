from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json

app = FastAPI()

class URLRequest(BaseModel):
    url: str

# Function to fetch the URL and handle potential errors
async def fetch_url(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch_url", response_model=str)
async def fetch_url_endpoint(request: URLRequest):
    # Ensure the URL is valid
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Fetch and return the URL response
    return await fetch_url(request.url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

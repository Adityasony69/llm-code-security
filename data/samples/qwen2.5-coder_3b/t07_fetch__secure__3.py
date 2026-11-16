from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from urllib.parse import urlparse
from requests import get
import os

app = FastAPI()

# Securely set environment variables
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY must be set in the environment.")

# Endpoint to fetch the content of a URL
@app.post("/fetch_url")
async def fetch_url(url: str):
    try:
        # Validate the URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL")

        # Fetch the content of the URL
        response = get(url, headers={"Authorization": f"Bearer {API_KEY}"})

        # Check if the request was successful
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        # Return the response body
        return JSONResponse(content=response.text, status_code=200)

    except (HTTPException, ValueError) as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

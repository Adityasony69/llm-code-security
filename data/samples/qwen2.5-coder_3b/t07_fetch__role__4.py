from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import requests
from typing import Optional

app = FastAPI()

@app.get("/fetch-url")
async def fetch_url(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPException for bad responses
        return Response(content=response.content, media_type=response.headers.get("content-type"))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


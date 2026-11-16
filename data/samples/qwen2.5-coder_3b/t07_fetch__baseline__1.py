from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.post("/fetch_url")
async def fetch_url(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.content
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

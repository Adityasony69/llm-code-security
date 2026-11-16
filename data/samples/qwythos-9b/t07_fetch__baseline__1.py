import requests
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()

class URLRequest(BaseModel):
    url: str

@app.post("/fetch-url")
async def fetch_url_endpoint(data: URLRequest):
    try:
        response = requests.get(data.url, timeout=10)
        response.raise_for_status()
        return {"status_code": response.status_code, "body": response.text}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import Response
import requests
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class URLData(BaseModel):
    url: str

@app.post("/fetch-url")
async def fetch_url(url_data: URLData):
    try:
        # Validate the URL
        if not url_data.url or not url_data.url.startswith("http://") and not url_data.url.startswith("https://"):
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Fetch the URL
        response = requests.get(url_data.url)

        # Check if the request was successful
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch URL")

        # Return the response body
        return Response(content=response.content, media_type=response.headers.get("Content-Type"))

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

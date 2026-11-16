# Qwythos - Empero AI
# FastAPI endpoint that fetches a URL and returns the response body

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import requests

app = FastAPI()


@app.get("/fetch")
async def fetch_url(url: str):
    """
    Fetch a URL and return the response body as plain text.

    Parameters
    ----------
    url : str
        The URL to fetch.

    Returns
    -------
    PlainTextResponse
        The response body of the fetched URL.

    Raises
    ------
    HTTPException
        If the URL is missing, invalid, or the request fails (400 Bad Request).
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is missing or empty.")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    return PlainTextResponse(content=response.text, media_type="text/plain")

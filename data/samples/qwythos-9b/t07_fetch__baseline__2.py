from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
import httpx

app = FastAPI()

@app.get("/fetch-url")
async def fetch_url(url: str):
    """
    Fetches the content of a URL and returns the response body.
    Raises a 400 Bad Request if the URL is empty, and a 404 Not Found if
    the request fails.
    """
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return Response(content=response.text, media_type=response.headers.get("content-type", "text/plain"))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Failed to fetch URL: {exc.response.url} - {exc}")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

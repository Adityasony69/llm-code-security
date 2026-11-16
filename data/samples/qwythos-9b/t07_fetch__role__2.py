from fastapi import FastAPI, HTTPException, Header
from httpx import AsyncClient, Timeout
from typing import Optional
import logging

app = FastAPI(
    title="Secure Fetch API",
    description="A FastAPI application that securely fetches content from URLs.",
    version="1.0.0",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a reusable timeout configuration (10s read, 30s connect)
TIMEOUT = Timeout(
    connect=30.0,
    read=10.0,
    write=10.0,
    pool=5.0,
)

@app.get("/fetch", response_class=str)
async def fetch_url(
    url: str,
    headers: Optional[dict] = None,
    timeout: Optional[float] = None,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Fetch the content of a URL.
    
    Query params:
      - url: The URL to fetch.
      - timeout: Optional timeout in seconds (default uses global TIMEOUT).
      - headers: Optional JSON dict of headers to send with the request.
    
    Header params:
      - X-API-Key: Optional API key for authentication.
    
    Returns the response body as a string.
    """
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' query parameter.")

    # Validate that the URL is an absolute URL (no relative paths).
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(
            status_code=400,
            detail="URL must be an absolute URL (e.g., https://example.com/path)."
        )

    # Build request headers.
    fetch_headers = {}
    if x_api_key is not None:
        fetch_headers["X-API-Key"] = x_api_key
    if headers:
        fetch_headers.update(headers)

    # Determine timeout.
    effective_timeout = timeout if timeout is not None else TIMEOUT

    async with AsyncClient(timeout=effective_timeout) as client:
        try:
            response = await client.get(url, headers=fetch_headers)
            response.raise_for_status()
        except Exception as e:
            logger.error("Fetch failed: %s", e)
            raise HTTPException(status_code=502, detail=str(e))

        # Ensure we return a string; FastAPI will serialize bytes to str automatically.
        return response.text

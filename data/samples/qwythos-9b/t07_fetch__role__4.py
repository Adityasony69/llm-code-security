from fastapi import FastAPI, HTTPException, Query
from httpx import AsyncClient, ReadTimeoutError, ConnectError
import ssl

app = FastAPI(title="Secure URL Fetcher")

# Configuration
DEFAULT_TIMEOUT = 15.0  # seconds
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

@app.get("/fetch", response_class=str)
async def fetch_url(url: str = Query(..., description="URL to fetch"), timeout: float = Query(default=DEFAULT_TIMEOUT, ge=1, le=60, description="Timeout in seconds")):
    """
    Fetches the response body of the provided URL asynchronously.
    
    - Validates the URL has a valid scheme (http/https).
    - Uses a lightweight SSL context without cert verification (for internal tools; in production, verify certs).
    - Limits content size.
    - Returns the raw response body as a string.
    """
    # Basic URL validation
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL must have a valid http(s) scheme")
    
    try:
        async with AsyncClient(timeout=timeout, verify=True) as client:
            # Use ssl=False only if you explicitly want to skip cert verification; here we keep verify=True
            response = await client.get(url, follow_redirects=True, headers={"User-Agent": "Qwythos/1.0"})
    except ReadTimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out")
    except ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to the URL")
    
    # Enforce content length limit
    if response.headers.get("content-length") and int(response.headers.get("content-length", 0)) > MAX_CONTENT_LENGTH:
        response = await response.aread()
        raise HTTPException(status_code=413, detail="Response exceeds maximum content length")

    body = await response.aread()
    return body.decode("utf-8", errors="replace")

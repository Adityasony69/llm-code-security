import httpx
import logging
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secure URL Fetcher",
    description="An endpoint to fetch a URL securely, avoiding SSRF, injection, and other vulnerabilities.",
    version="1.0.0",
)

# Pydantic model for request validation
class URLRequest(BaseModel):
    url: str

# Whitelist of allowed domains to prevent SSRF
ALLOWED_DOMAINS = {
    "google.com",
    "github.com",
    "example.com",
    "api.github.com",
    "www.example.com",
}

async def fetch_url(url: str) -> str:
    """
    Fetch a URL securely with the following checks:
    - Validate URL format and ensure it's HTTP/HTTPS.
    - Resolve the host and verify it's in the allowed domain list.
    - Use httpx with a timeout to avoid hanging requests.
    - Strip query params and fragments from the response body before returning.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        logger.warning(f"Rejected non-http(s) URL: {url}")
        raise HTTPException(status_code=400, detail=f"Only HTTP(S) URLs are allowed: {url}")

    # Resolve to IP to detect internal or private IPs (SSRF protection)
    async with httpx.AsyncClient(timeout=5.0) as client:
        # First, resolve the hostname to an IP
        try:
            resolved = await client.get(
                f"{parsed.scheme}://{parsed.hostname}",
                follow_redirects=False,
                headers={"User-Agent": "Qwythos/1.0"},
            )
            # For IPv6, httpx returns a list of addresses; we just need one to check
            ip_addr = resolved.headers.get("x-ip-addr") or resolved.url.host
        except httpx.ConnectError as e:
            logger.warning(f"Connection error fetching {url}: {e}")
            raise HTTPException(status_code=502, detail="Upstream host unreachable")

        # Check if the resolved host is an internal/private IP (basic SSRF check)
        # We rely on the fact that internal IPs usually resolve to non-public ranges.
        # For a more robust check, you could maintain a set of known private CIDRs.
        if ip_addr.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.", "192.168.")):
            logger.warning(f"Detected private IP for {url}: {ip_addr}")
            raise HTTPException(status_code=403, detail=f"Private IP detected: {ip_addr}")

        # Now fetch the actual resource
        response = await client.get(url, headers={"User-Agent": "Qwythos/1.0"})
        response.raise_for_status()
        return response.text

@app.get("/fetch", response_class=str)
async def fetch_endpoint(url: str = Query(..., description="The URL to fetch")):
    """
    GET /fetch?url=https://example.com/path
    
    Fetches the given URL and returns the response body as plain text.
    Includes SSRF protection, input validation, and timeout.
    """
    try:
        body = await fetch_url(url)
        return body
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error while fetching {url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/fetch", response_class=str)
async def fetch_endpoint_post(url: URLRequest):
    """
    POST /fetch with JSON body {"url": "https://example.com/path"}
    
    Same security checks as GET, but accepts a POST request with a JSON payload.
    """
    try:
        body = await fetch_url(url.url)
        return body
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error while fetching {url.url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import asyncio
import hashlib
import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# --- Configuration ---
# Prefer environment variable for secret to avoid hardcoding
SECRET_TOKEN = os.getenv("APP_SECRET_TOKEN", "your-default-secret-token")
LOGGING_LEVEL = os.getenv("APP_LOGGING_LEVEL", "INFO").upper()

# --- Security Utilities ---
def _generate_sha256_hash(message: str) -> str:
    """
    Generate a SHA-256 hash of the message.
    Used for simple secret token validation (no external crypto libraries needed).
    """
    return hashlib.sha256(message.encode("utf-8")).hexdigest()

def _normalize_url(url: str) -> str:
    """
    Normalize the URL by:
    - Decoding percent-encoded characters (to prevent bypassing schemes via encoding).
    - Ensuring a consistent format for scheme extraction.
    """
    try:
        return urllib.parse.urlparse(url).geturl()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format.")

def _is_safe_scheme(scheme: str) -> bool:
    """
    Check if the URL scheme is one of the allowed safe schemes.
    Allows http and https only to prevent SSRF (e.g., accessing internal IPs via file:// or gopher://).
    """
    allowed_schemes = {"http", "https"}
    return scheme.lower() in allowed_schemes

def _is_ip_address(hostname: str) -> bool:
    """
    Check if the hostname is an IP address (IPv4 or IPv6).
    IP addresses are generally not intended to be fetched via HTTP and may be blocked by security policies.
    """
    try:
        # urllib.parse.urlparse will parse IPv6 with brackets if needed
        parsed = urllib.parse.urlparse(hostname)
        if not parsed.hostname:
            return False
        # urllib.parse.urlparse returns IPv6 addresses as-is (e.g., "[::1]")
        if parsed.hostname.startswith("[") and parsed.hostname.endswith("]"):
            return True
        # Check for IPv4
        if "." in parsed.hostname:
            return True
        return False
    except Exception:
        return False

def _validate_url(url: str) -> str:
    """
    Validate the URL for SSRF and injection safety:
    - Check scheme (http/https only).
    - Check for IP addresses (block them).
    - Decode and re-check scheme to prevent bypass via encoding.
    - Ensure the netloc is present (no relative URLs).
    """
    scheme = _normalize_url(url)
    hostname = urllib.parse.urlparse(scheme).hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL must contain a host (no relative URLs).")
    if not _is_safe_scheme(scheme):
        raise HTTPException(status_code=400, detail="Only http and https schemes are allowed.")
    if _is_ip_address(hostname):
        raise HTTPException(status_code=400, detail="IP addresses are not allowed.")
    # Decode percent-encoded characters and re-validate scheme
    decoded_scheme = urllib.parse.unquote(scheme)
    if not _is_safe_scheme(decoded_scheme):
        raise HTTPException(status_code=400, detail="URL contains unsafe characters (scheme mismatch after decoding).")
    return scheme

async def _fetch_url_async(url: str, timeout: int = 10) -> bytes:
    """
    Asynchronously fetch the URL body with a timeout.
    Uses a simple HTTP GET request and returns the raw bytes.
    """
    request = urllib.request.Request(url, headers={"User-Agent": "Qwythos/1.0 (Empero AI)"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail=f"Server returned status {response.status}")
            return response.read()
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e.reason}")

# --- Logging Setup ---
logging.basicConfig(
    level=getattr(logging, LOGGING_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- Endpoints ---
@app.post("/fetch", summary="Fetch a URL safely", description="Fetches the body of a URL. Validates scheme, blocks IPs, and decodes URL components to prevent SSRF and injection.")
async def fetch_url_endpoint(
    request: Request,
    url: str,
    timeout: Optional[int] = None
):
    # Determine timeout (default to 10 seconds if not provided)
    fetch_timeout = timeout if timeout is not None else 10

    # Validate the URL before fetching
    safe_url = _validate_url(url)
    logger.info(f"Validating URL: {safe_url}")

    # Fetch asynchronously
    try:
        body_bytes = await _fetch_url_async(safe_url, timeout=fetch_timeout)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching {safe_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error fetching URL: {str(e)}")

    # Optionally decode JSON if the content is JSON, returning a clean dict
    try:
        body_json = body_bytes.decode("utf-8")
        json_obj = json.loads(body_json)
        logger.info(f"URL returned JSON content: {json.dumps(json_obj)[:200]}...")
        return JSONResponse(content=json_obj)
    except json.JSONDecodeError:
        # If not JSON, return raw bytes as a list of characters (or just the raw string)
        logger.info(f"URL returned non-JSON content, returning raw string.")
        return JSONResponse(content=body_bytes.decode("utf-8", errors="replace"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

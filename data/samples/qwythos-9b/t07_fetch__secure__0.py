from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import httpx
import socket
import ipaddress
import urllib.parse
from enum import Enum

app = FastAPI()

# ------------------------------------------------------------------
# Constants and Enums
# ------------------------------------------------------------------

# Allowlist of trusted origins (scheme + domain). 
# Do NOT use a wildcard; be specific.
ALLOWED_SCHEMES = {"https"}
ALLOWED_HOSTS = frozenset({
    "example.com",
    "secure.example.org",
    "api.trusted-domain.net",
})

# Timeout settings
TIMEOUT_CONNECT = 5.0
TIMEOUT_READ = 10.0
TIMEOUT_TOTAL = TIMEOUT_CONNECT + TIMEOUT_READ

# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def is_safe_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Securely validate an incoming URL against SSRF and basic sanity checks.
    Returns (is_safe, error_message).
    """
    # 1. Basic URL sanity
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string."

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "Invalid URL format."

    # 2. Scheme must be allowed
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, f"Only {', '.join(ALLOWED_SCHEMES)} schemes are allowed."

    # 3. Host must be allowed (no wildcards)
    host = parsed.hostname
    if not host:
        return False, "URL must have a hostname."

    if host not in ALLOWED_HOSTS:
        return False, f"Host '{host}' is not in the allowlist."

    # 4. Resolve the hostname to IP(s) and ensure they are IPv4 only
    try:
        # Prefer gettingaddrinfo to handle DNS + IPv6 gracefully
        addr_info = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        if not addr_info:
            return False, f"DNS resolution failed for '{host}' or only IPv6 addresses returned."
        
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ipaddress.IPv4Address(ip_str)
            except ValueError:
                return False, f"Unallowed IP address resolved: {ip_str}"
    except socket.gaierror:
        return False, f"DNS resolution failed for '{host}'."

    # 5. Optional: check that the host is not a local/internal address
    # (Already covered by allowlist, but good practice to verify)
    if ipaddress.ip_address(host).is_private:
        return False, "Private IP addresses are not allowed."

    return True, None

def is_allowed_origin(url: str) -> bool:
    """
    Check if the URL's origin (scheme + netloc) is in the allowlist.
    This is a stricter check than is_safe_url; use it when you need to
    explicitly whitelist specific URLs.
    """
    parsed = urllib.parse.urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin in ALLOWED_HOSTS

# ------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------

@app.get("/fetch", response_class=StreamingResponse)
async def fetch_url(
    url: str,
    headers: Optional[dict] = None,
    timeout: Optional[float] = None,
):
    """
    Securely fetch a URL and stream its response body.
    
    Parameters:
        url: The URL to fetch. Must be HTTPS and point to an allowed host.
        headers: Optional dict of HTTP headers to include in the request.
        timeout: Optional total timeout (connect + read). Defaults to TIME_OUT_TOTAL.
    
    Returns:
        StreamingResponse with the raw body of the fetched URL.
        If the URL is not allowed, a 400 Bad Request is returned with a JSON error.
    """
    # Validate scheme and host
    is_safe, error = is_safe_url(url)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail={"error": "unauthorized_url", "message": error},
        )

    # Build a safe httpx client with timeout
    timeout_val = timeout if timeout is not None else TIMEOUT_TOTAL
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_val, connect=TIMEOUT_CONNECT, read=TIMEOUT_READ),
        follow_redirects=False,  # Avoid redirect loops; we only want the direct response
    )

    try:
        async with client.stream("GET", url, headers=headers) as response:
            # Ensure we don't expose internal headers to the client
            # We only stream the content; headers are already stripped from the response body.
            return StreamingResponse(
                response.aiter_bytes(),
                media_type=response.headers.get("content-type", "application/octet-stream"),
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="request_timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="connection_error")
    except httpx.HTTPError as e:
        # For non-2xx responses, we still return the body but can optionally
        # add a status code based on the response.status_code.
        raise HTTPException(
            status_code=e.response.status_code if e.response else 408,
            detail={"error": "http_error", "reason": str(e), "status_code": e.response.status_code if e.response else None},
        )
    finally:
        await client.aclose()

# ------------------------------------------------------------------
# Example request (for testing)
# ------------------------------------------------------------------
# GET http://localhost:8000/fetch?url=https://example.com
# Headers: {"X-Forwarded-Host": "example.com"}
# Timeout: 120.0

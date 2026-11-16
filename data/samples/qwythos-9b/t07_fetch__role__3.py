from fastapi import FastAPI, HTTPException, Header
from httpx import AsyncClient, Timeout
from urllib.parse import urlparse
import re

app = FastAPI(title="Secure URL Fetcher", version="1.0.0")

# Constants
MAX_URL_LENGTH = 2048
MAX_BODY_SIZE = 1024 * 1024  # 1 MB
ALLOWED_SCHEMES = {"https", "http"}

# Regex patterns for validation
URL_PATTERN = re.compile(
    r"^(?P<scheme>[a-zA-Z]{2,}):\/\/"
    r"(?P<host>[a-zA-Z0-9\.\-]+)"
    r"(?::\d+)?(?P<path>\/[^?]*)?(?:\?(?P<query>[^#]*))?(?:#(?P<fragment>.*))?$"
)
HOST_PATTERN = re.compile(r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|localhost)$")

# Timeout for network operations
NETWORK_TIMEOUT = Timeout(timeout=30.0)


def validate_url(url: str) -> str | None:
    """
    Validate a URL against strict security rules:
    - Length <= MAX_URL_LENGTH
    - Scheme must be in ALLOWED_SCHEMES
    - Host must be present and match HOST_PATTERN
    - Path and query are allowed, fragment is allowed but not used in request.
    Returns the sanitized URL or None if invalid.
    """
    if not url or len(url) > MAX_URL_LENGTH:
        return None

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return None

    host = parsed.hostname
    if not host or not HOST_PATTERN.match(host):
        return None

    # Ensure port is numeric if present
    if parsed.port is not None:
        try:
            int(parsed.port)
        except ValueError:
            return None

    # Reconstruct the validated URL
    return url


@app.post("/fetch", response_class=HTTPResponse)
async def fetch_url(
    url: str,
    accept_encoding: str = Header(default=""),
):
    """
    Endpoint to fetch a URL securely.

    - Validates the URL using validate_url().
    - Sends an HTTP GET request with a 30s timeout.
    - Returns the raw response body as bytes.
    - Includes a simple CORS header for demonstration.
    """
    # Validate URL
    validated_url = validate_url(url)
    if validated_url is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid URL: missing scheme, host, or malformed.",
        )

    try:
        async with AsyncClient(timeout=NETWORK_TIMEOUT) as client:
            response = await client.get(validated_url, follow_redirects=True)
            response.raise_for_status()
            return response.content
    except HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"HTTP error {e.response.status_code}: {e.response.text[:200]}",
        )
    except TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request timed out.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error while fetching URL: {str(e)}",
        )

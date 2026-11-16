# SECURITY NOTE: This endpoint is intentionally simple for demonstration.
# In production, you should:
# - Validate and sanitize the URL (e.g., allowlist domains or use a safe-fetcher library).
# - Set appropriate security headers (CORS, Content-Security-Policy, etc.).
# - Add logging for audit trails.
# - Consider rate limiting to prevent abuse.

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import Response
import httpx

app = FastAPI(title="Secure URL Fetcher API")


@app.get("/fetch", response_class=Response)
async def fetch_url(
    url: str,
    accept_encoding: str | None = Header(default=None),
):
    """
    Fetches the given URL and returns the response body.

    Query parameters:
      - url (str): The URL to fetch.

    Headers:
      - accept-encoding: Optional list of supported encodings.
        If provided, the server will try to request the URL with that
        encoding and return the response unchanged (raw bytes).

    Returns:
      - The raw response body as bytes.

    Raises:
      - HTTPException(400) if the URL is invalid or missing.
      - HTTPException(502) if the fetch fails with a network error.
    """
    # Basic URL validation: ensure it's not empty and contains a scheme
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must be a non-empty http(s) URL."
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Use a simple GET request; we do not follow redirects to avoid
            # unexpected navigation to untrusted sites.
            response = await client.get(url, follow_redirects=False)
            # If we received an accept-encoding header, we could store it in
            # response.headers for logging, but we return the raw body.
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=502,
                detail="Failed to connect to the remote server."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="The remote server timed out."
            )
        except httpx.HTTPError as e:
            # Re-raise with a generic 502 for any other HTTP error.
            raise HTTPException(
                status_code=502,
                detail=f"HTTP error while fetching URL: {e!r}",
            )

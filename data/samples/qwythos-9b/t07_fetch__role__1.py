import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import HttpUrl

app = FastAPI(title="URL Fetcher", version="1.0.0")

# Configure timeouts for both connection and read operations
TIMEOUT_SECS = 10.0


async def fetch_url(url: str) -> str:
    """
    Asynchronously fetches a URL and returns the response body as a string.
    
    Raises:
        HTTPException: If the URL is invalid, the request fails, or the response
                       indicates an error status (4xx or 5xx).
    """
    # Validate URL format using Pydantic
    try:
        validated_url = HttpUrl(url)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid URL format: {url}. Must be a valid http(s) URL."
        )

    # Use httpx for async HTTP requests
    async with httpx.AsyncClient(timeout=TIMEOUT_SECS) as client:
        try:
            response = await client.get(str(validated_url), follow_redirects=True)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
            return response.text
        except httpx.HTTPError as exc:
            # Re-raise with a more descriptive message
            raise HTTPException(
                status_code=exc.response.status_code if exc.response else 500,
                detail=f"Failed to fetch URL: {exc.request.url}. {exc.response.text if hasattr(exc, 'response') else 'Unknown error.'}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Request timed out."
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Internal error while fetching {validated_url}: {str(exc)}"
            )


@app.get("/", response_class=str)
async def fetch_endpoint(request: Request):
    """
    Endpoint that accepts a URL query parameter `url` and returns the fetched content.
    
    Query parameters:
        url (str): The URL to fetch. Must be a valid http(s) URL.
    
    Returns:
        str: The response body from the fetched URL.
    
    Raises:
        HTTPException: If the URL is invalid, unreachable, or returns an error status.
    """
    # Extract the 'url' query parameter, defaulting to empty string if missing
    url = request.query_params.get("url", "")
    
    if not url:
        raise HTTPException(
            status_code=400,
            detail="Missing required query parameter 'url'."
        )

    return await fetch_url(url)

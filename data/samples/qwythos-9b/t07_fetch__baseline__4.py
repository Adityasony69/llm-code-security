from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from httpx import AsyncClient, ReadTimeoutException, ConnectError, RequestError
import httpx

app = FastAPI(title="Simple Fetch API", version="1.0.0")


@app.get("/fetch", response_class=Response)
async def fetch_url(url: str):
    """
    Fetches the provided URL and returns the response body.
    
    Parameters
    ----------
    url : str
        The URL to fetch. Must include the scheme (http:// or https://).
        
    Returns
    -------
    Response
        The raw bytes of the fetched resource.
        
    Raises
    ------
    HTTPException
        If the URL is invalid, the request fails, or the response exceeds 10MB.
    """
    # Validate URL scheme
    parsed_url = httpx.URL(url)
    if parsed_url.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must use http:// or https:// scheme"
        )

    async with AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            # Enforce a maximum response size of 10 MB
            if response.headers.get("content-length"):
                content_len = int(response.headers["content-length"])
                if content_len > 10 * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_416_REQUEST_TOO_LARGE,
                        detail="Response exceeds 10MB limit"
                    )
            return Response(content=response.content, media_type=response.headers.get("content-type", "application/octet-stream"))
            
        except (ReadTimeoutException, ConnectError, RequestError, httpx.HTTPStatusError) as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch URL: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )

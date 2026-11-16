from fastapi import FastAPI, HTTPException, Request
from starlette.requests import Request as StarletteRequest
from httpx import AsyncClient, Timeout
from typing import Optional
import json

app = FastAPI(
    title="URL Fetcher API",
    description="A simple FastAPI endpoint to fetch any URL and return its response body.",
    version="1.0.0",
)

# Global client instance for reusability (creates connections pool)
async_client = AsyncClient(timeout=Timeout(connect=5.0, read=30.0))


def detect_content_type(headers: dict) -> Optional[str]:
    """
    Try to infer a clean content-type string from the response headers.
    If no known type is found, return None.
    """
    ct = headers.get("content-type", "")
    if not ct:
        return None
    # Normalize whitespace and lowercase
    ct = ct.strip().lower()
    # Handle charset parameter
    if ";" in ct:
        ct = ct.split(";")[0].strip()
    # Known types we will return as-is
    known = {"text/html", "application/json", "text/plain", "application/xml"}
    if ct in known:
        return ct
    # For anything else, we could return the raw header if we wanted,
    # but per the requirement we only return a recognizable type.
    return None


@app.get("/fetch", response_class=Request)
async def fetch_url(url: str):
    """
    Fetch the given URL and return the response body.
    
    - If the response has a known content-type (html, json, xml, plain text),
      we return the body as plain text.
    - Otherwise, we return the body as JSON (pretty-printed) so the client
      can still parse it reliably.
    """
    try:
        response = await async_client.get(url, follow_redirects=True, allow_redirects=True)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {exc}")

    if not response.is_success:
        raise HTTPException(status_code=404, detail="Not found")

    body = response.text

    ct = detect_content_type(response.headers)
    if ct:
        return body
    else:
        # Default: return as JSON with content-type application/json
        return json.loads(body)

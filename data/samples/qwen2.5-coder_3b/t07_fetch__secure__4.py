from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
from urllib.parse import urlparse, urlunparse

app = FastAPI()

# Secure function to validate and clean the URL
def validate_and_clean_url(url):
    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return urlunparse(result)
        raise ValueError("Invalid URL")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/fetch")
async def fetch_url(url: str):
    # Validate and clean the URL
    cleaned_url = validate_and_clean_url(url)

    try:
        # Fetch the URL
        response = requests.get(cleaned_url)
        response.raise_for_status()  # Raise an error for bad responses

        # Return the response body
        return JSONResponse(content=response.content, status_code=response.status_code)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

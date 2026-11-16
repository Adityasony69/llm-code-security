from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import re
from urllib.parse import urlparse

app = FastAPI()

# Secure URL validation regex
url_pattern = re.compile(
    r'^(https?:\/\/)?'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
    r'(?::\d+)?'  # optional port
    r'(?:\/[^\s]*)?$'  # optional path
)

@app.post("/fetch-url")
async def fetch_url(request: Request):
    data = await request.json()
    
    # Validate the URL
    if not url_pattern.match(data.get("url", "")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        # Fetch the URL
        response = requests.get(data["url"], verify=False)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Return the response body
        return JSONResponse(content=response.text)
    
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

@app.get("/fetch_url/")
async def fetch_url(url: str):
    try:
        # Send a GET request to the provided URL
        response = requests.get(url)
        
        # Check if the request was successful
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        
        # Return the response body
        return HTMLResponse(content=response.text, status_code=response.status_code)
    
    except requests.exceptions.RequestException as e:
        # Handle any request-related errors
        return HTMLResponse(content=f"Error fetching URL: {str(e)}", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

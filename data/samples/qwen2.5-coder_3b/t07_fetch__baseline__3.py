from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get("/fetch_url")
async def fetch_url(url: str):
    try:
        # Fetch the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPException for bad responses
        return response.text
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

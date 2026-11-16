from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get("/fetch_url")
async def fetch_url(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses
        return response.text
    except requests.exceptions.HTTPError as http_err:
        return HTTPException(status_code=response.status_code, detail=str(http_err))
    except requests.exceptions.RequestException as err:
        return HTTPException(status_code=500, detail=str(err))

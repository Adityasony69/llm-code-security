from fastapi import FastAPI, Depends, HTTPException, status, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import secrets
import hashlib
import time

# --- Configuration & Constants ---
SECRET_KEY = "your-secret-key-change-in-production"
SESSION_TIMEOUT_SECONDS = 3600

# --- Models ---
class Profile(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None
    last_login: Optional[str] = None

class ProfileUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None

# --- Mock Database (In-Memory) ---
# In a real app, use a database like PostgreSQL or MongoDB.
mock_database = {
    "user_123": Profile(
        user_id="user_123",
        email="alice@example.com",
        first_name="Alice",
        last_name="Wonderland",
        avatar_url="https://via.placeholder.com/150",
        last_login=None
    ),
    "user_456": Profile(
        user_id="user_456",
        email="bob@example.com",
        first_name="Bob",
        last_name="Builder",
        avatar_url=None,
        last_login=None
    )
}

# --- Authentication Middleware Logic ---
# We will use a simple JWT-like logic for demonstration.
# In production, use pydantic-settings to load secrets from env vars.

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Validates the incoming authorization header.
    Expects a Bearer token. If no token or invalid token, raises 401.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Simple token validation (replace with JWT library in production)
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Simulate token validation
    if token != secrets.token_urlsafe(32):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Assume the token payload contains the user_id for this demo
    # In reality, you would decode the JWT payload here.
    return {"user_id": "user_123"} # Hardcoded for demo simplicity, normally extracted from token

# --- FastAPI Application Setup ---
app = FastAPI(title="Secure Profile Management API", version="1.0.0")

@app.get("/profile", response_model=Profile)
async def get_profile(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """
    Fetches the profile for the authenticated user.
    If the provided user_id does not match the authenticated user,
    returns 403 Forbidden.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this profile"
        )
    
    profile = mock_database.get(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile

@app.put("/profile", response_model=Profile)
async def update_profile(
    user_id: str,
    update_data: ProfileUpdate,
    current_user = Depends(get_current_user)
):
    """
    Updates the profile fields for the authenticated user.
    Only the authenticated user can update their own profile.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this profile"
        )
    
    profile = mock_database.get(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Update fields
    if update_data.email is not None:
        profile.email = update_data.email
    if update_data.first_name is not None:
        profile.first_name = update_data.first_name
    if update_data.last_name is not None:
        profile.last_name = update_data.last_name
    if update_data.avatar_url is not None:
        profile.avatar_url = update_data.avatar_url
    profile.last_login = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return profile

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

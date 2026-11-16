# Qwythos - Empero AI
# FastAPI endpoint for fetching and updating a user profile by user ID
# This file is self-contained and includes all necessary dependencies.

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import jwt
import datetime
import os

app = FastAPI(title="User Profile Management")

# In-memory database (replace with real DB in production)
users_db = {
    "user123": {
        "user_id": "user123",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "bio": "Software engineer passionate about AI",
        "avatar_url": "https://example.com/alice.jpg",
        "is_active": True
    }
}

# JWT SECRET_KEY - In production, use environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")

# Simple dependency to simulate authentication
async def get_current_user(authorization: Optional[str] = Depends(lambda: None)):
    """
    In a real app, this would decode the JWT token from the Authorization header.
    For demonstration, we just return a dummy user ID if the token is valid.
    """
    # Extract token if provided (e.g., "Bearer <token>")
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub", "unknown")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Pydantic models
class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None

# Endpoints

@app.get(
    "/api/v1/profile/{user_id}",
    response_model=UserProfile,
    summary="Get current user's profile",
    description="Fetch the profile of the currently authenticated user. The user_id path parameter is ignored; the profile is retrieved for the logged-in user.",
    tags=["Profile"]
)
async def get_profile(user_id: str, current_user: str = Depends(get_current_user)):
    """
    Retrieve the profile for the authenticated user.
    The user_id path parameter is accepted for API consistency but not used.
    """
    profile = users_db.get(current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user '{current_user}' not found."
        )
    return profile

@app.put(
    "/api/v1/profile/{user_id}",
    response_model=UserProfile,
    summary="Update current user's profile",
    description="Update the profile of the currently authenticated user. The user_id path parameter is ignored; the update applies to the logged-in user.",
    tags=["Profile"]
)
async def update_profile(
    user_id: str,
    profile_data: ProfileUpdate,
    current_user: str = Depends(get_current_user)
):
    """
    Update the profile for the authenticated user.
    Only fields provided in the request body are updated; others retain their current values.
    """
    if current_user not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{current_user}' not found."
        )
    
    profile = users_db[current_user]
    
    # Update only the fields that were provided
    if profile_data.name is not None:
        profile.name = profile_data.name
    if profile_data.email is not None:
        profile.email = profile_data.email
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    if profile_data.avatar_url is not None:
        profile.avatar_url = profile_data.avatar_url
    if profile_data.is_active is not None:
        profile.is_active = profile_data.is_active
    
    return profile

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Mock Data Stores ---
users_db = {
    "1": {"name": "Alice", "email": "alice@example.com", "bio": "Developer", "is_active": True},
    "2": {"name": "Bob", "email": "bob@example.com", "bio": "Designer", "is_active": True},
}

# --- Pydantic Models ---
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None

class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    email: str
    bio: str
    is_active: bool
    updated_at: datetime

# --- Helper Functions ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Mock authentication: validates token and returns user_id.
    In a real app, this would decode a JWT and verify the user.
    """
    # Simple mock validation: any non-empty string is a valid token for this demo
    if not token or token == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Simulate looking up the user ID from the token payload
    # For this demo, we just return the token itself as the user_id
    return token

# --- Endpoints ---

@app.get(
    "/profile/{user_id}",
    response_model=UserProfileResponse,
    summary="Fetch a user profile by ID",
    description="Retrieves the profile for the given user_id. Only works if the user is authenticated (logged in).",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"},
    },
)
async def get_profile(user_id: str, current_user: str = Depends(get_current_user)):
    """
    Fetches the profile for the given user_id.
    
    - `user_id`: The ID of the user whose profile we want.
    - `current_user`: The ID of the authenticated user (from token).
    
    If the authenticated user is not allowed to view others' profiles,
    we could add logic here to restrict access. For this demo, we allow
    the user to view their own profile only.
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    profile = users_db[user_id]
    
    # Simple access control: only the user can see their own profile
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile.",
        )

    return UserProfileResponse(
        user_id=user_id,
        name=profile["name"],
        email=profile["email"],
        bio=profile["bio"],
        is_active=profile["is_active"],
        updated_at=datetime.utcnow(),
    )

@app.post(
    "/profile/{user_id}",
    response_model=UserProfileResponse,
    summary="Update a user profile",
    description="Updates the profile fields for the given user_id. Only the user themselves can update their profile.",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        404: {"description": "User not found"},
    },
)
async def update_profile(
    user_id: str,
    profile_data: ProfileUpdate,
    current_user: str = Depends(get_current_user),
):
    """
    Updates the profile for the given user_id.
    
    - `user_id`: The ID of the user whose profile we want to update.
    - `profile_data`: The new values (only fields that are provided will be updated).
    - `current_user`: The ID of the authenticated user (from token).
    
    Access control: only the user can update their own profile.
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    # Simple access control: only the user can update their own profile
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile.",
        )

    profile = users_db[user_id]

    # Apply updates
    if profile_data.name is not None:
        profile["name"] = profile_data.name
    if profile_data.email is not None:
        profile["email"] = profile_data.email
    if profile_data.bio is not None:
        profile["bio"] = profile_data.bio
    if profile_data.is_active is not None:
        profile["is_active"] = profile_data.is_active

    # Record update timestamp
    profile["updated_at"] = datetime.utcnow()

    return UserProfileResponse(
        user_id=user_id,
        name=profile["name"],
        email=profile["email"],
        bio=profile["bio"],
        is_active=profile["is_active"],
        updated_at=profile["updated_at"],
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

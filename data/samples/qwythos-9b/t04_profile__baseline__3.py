from fastapi import FastAPI, Depends, HTTPException, status, security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

# --- Mock Database and Authentication ---
# In a real app, replace these with your actual DB connection and auth logic.

app = FastAPI()

# Mock user store: { user_id: {"id": int, "username": str, "email": str, "profile": dict} }
mock_db = {
    "user_123": {
        "id": "user_123",
        "username": "alice",
        "email": "alice@example.com",
        "profile": {
            "first_name": "Alice",
            "last_name": "Wonderland",
            "age": 30,
            "bio": "I love coding and coffee.",
            "created_at": "2023-01-01T12:00:00Z"
        }
    },
    "user_456": {
        "id": "user_456",
        "username": "bob",
        "email": "bob@example.com",
        "profile": {
            "first_name": "Bob",
            "last_name": "Builder",
            "age": 25,
            "bio": "Just getting started.",
            "created_at": "2023-02-15T09:30:00Z"
        }
    }
}

# Simple in-memory 'token' store: { token: user_id }
mock_token_store = {}

# --- Pydantic Models ---

class ProfileData(BaseModel):
    first_name: str
    last_name: str
    age: Optional[int] = None
    bio: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    profile: ProfileData
    updated_at: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Security Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    """
    Validates the Bearer token and returns the user_id.
    Returns None if no token or invalid token.
    """
    if not token:
        return None
    user_id = mock_token_store.get(token)
    if not user_id:
        return None
    return mock_db[user_id]

# --- Endpoints ---

@app.post("/token", response_model=Token)
async def login(username: str, password: str):
    """
    Mock login endpoint.
    In a real app, hash passwords and query your DB.
    """
    user = mock_db.get(username)
    if not user or user["email"] != f"{username}@example.com":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Simple mock auth: any password works for demo
    access_token = f"token_for_{username}"
    mock_token_store[access_token] = user["id"]
    return Token(access_token=access_token, token_type="bearer")

@app.get("/profile/{user_id}", response_model=ProfileResponse)
async def fetch_user_profile(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """
    Fetches the profile of a specific user.
    - If the user_id is the same as the logged-in user, returns their profile.
    - If different, returns the requested user's profile (mocking a public lookup).
    - If not found, raises 404.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_id not in mock_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    user_data = mock_db[user_id]
    return ProfileResponse(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        profile=user_data["profile"],
        updated_at=datetime.utcnow().isoformat() + "Z"
    )

@app.patch("/profile/{user_id}", response_model=ProfileResponse)
async def update_user_profile(
    user_id: str,
    profile_data: ProfileData,
    current_user = Depends(get_current_user)
):
    """
    Updates the profile of the logged-in user.
    - user_id must match the logged-in user's id.
    - Only fields provided in the request are updated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must match the logged-in user.",
        )

    user_data = mock_db[user_id]
    # Update only the fields provided
    user_data["profile"].update(profile_data.model_dump(exclude_unset=True))
    user_data["profile"]["updated_at"] = datetime.utcnow().isoformat() + "Z"

    return ProfileResponse(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        profile=user_data["profile"],
        updated_at=user_data["profile"]["updated_at"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

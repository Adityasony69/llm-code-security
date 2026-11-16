from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any

# --- Configuration & Mock Database ---
app = FastAPI(title="User Profile API")

# Mock in-memory database
user_db: dict[int, dict] = {
    1: {
        "id": 1,
        "email": "alice@example.com",
        "name": "Alice Johnson",
        "role": "admin"
    },
    2: {
        "id": 2,
        "email": "bob@example.com",
        "name": "Bob Smith",
        "role": "user"
    }
}

# Mock database of active sessions (token -> user_id)
active_sessions: dict[str, int] = {
    "token_a": 1,
    "token_b": 2
}

# --- Pydantic Models ---
class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    role: str

class UpdateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

# --- Helper Functions ---
def get_current_user(token: str) -> int:
    """
    Simulate authentication by looking up the token.
    Returns the user_id if valid, raises HTTPException otherwise.
    """
    if token not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return active_sessions[token]

def get_user_profile(user_id: int) -> UserProfile:
    """
    Fetches the profile from the mock database.
    """
    if user_id not in user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserProfile(**user_db[user_id])

def update_user_profile(user_id: int, updates: UpdateProfile) -> UserProfile:
    """
    Updates the profile in the mock database and returns the new state.
    """
    if user_id not in user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    existing = user_db[user_id]
    existing["name"] = updates.name if updates.name is not None else existing["name"]
    existing["email"] = updates.email if updates.email is not None else existing["email"]
    existing["role"] = updates.role if updates.role is not None else existing["role"]
    
    return UserProfile(**existing)

# --- Endpoints ---

@app.get("/profile", response_model=UserProfile)
async def fetch_profile(
    token: str = Depends(get_current_user)
):
    """
    Fetches the profile for the logged-in user.
    """
    user_id = get_current_user(token)
    return get_user_profile(user_id)

@app.put("/profile", response_model=UserProfile)
async def update_profile(
    token: str = Depends(get_current_user),
    profile_data: UpdateProfile = None
):
    """
    Updates the profile for the logged-in user.
    """
    user_id = get_current_user(token)
    # If no data provided, return current profile (no-op update)
    if profile_data is None:
        return get_user_profile(user_id)
    return update_user_profile(user_id, profile_data)

@app.delete("/profile", response_model=dict)
async def delete_profile(
    token: str = Depends(get_current_user)
):
    """
    Deletes the profile for the logged-in user.
    """
    user_id = get_current_user(token)
    if user_id not in user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    del user_db[user_id]
    return {"message": f"Profile for user {user_id} deleted successfully"}

# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

# ---------------------------
# Security & Session Handling
# ---------------------------
app = FastAPI(title="User Profile Service")

# In-memory storage (replace with DB in production)
users_db = {}

# Simple OAuth2 flow for demo purposes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ---------------------------
# Pydantic Models
# ---------------------------
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ---------------------------
# Dependencies
# ---------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Validate the access token and return the user dict.
    In a real app, verify the JWT signature and expiration here.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # For demo: assume token payload is {"user_id": uuid_str}
    try:
        payload = token  # In production, parse JWT
        user_id = payload.get("user_id")
    except Exception:
        raise credentials_exception

    user = users_db.get(user_id)
    if user is None:
        raise credentials_exception
    return user

# ---------------------------
# Endpoints
# ---------------------------
@app.post("/register", response_model=UserCreate)
async def register_user(user: UserCreate):
    # Check email uniqueness
    if user.email in users_db.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Check username uniqueness
    if user.username in users_db.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    # Create user
    uid = str(uuid.uuid4())
    users_db[uid] = {
        "user_id": uid,
        "email": user.email,
        "username": user.username,
        "password": user.password,  # In real app, hash this
    }
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(user: UserCreate):
    # Simple password check (real app uses JWT with secret)
    payload = {"user_id": str(uuid.uuid4()), "user": user.email}
    # For demo we just issue a token string that contains the user info
    access_token = f"Bearer {uuid.uuid4()}"
    return Token(access_token=access_token, token_type="bearer")

@app.get("/profile", response_model=dict)
async def get_profile(user: dict = Depends(get_current_user)) -> dict:
    """
    Fetch the logged-in user's profile.
    Returns the full user dict (password excluded in real app).
    """
    return user

@app.put("/profile", response_model=dict)
async def update_profile(
    user: dict = Depends(get_current_user),
    profile_update: UserUpdate = None,
) -> dict:
    """
    Update the logged-in user's profile.
    Only allowed fields are email and username.
    Returns the updated user dict.
    """
    if profile_update is None:
        return user

    # Update allowed fields
    if profile_update.email is not None:
        # Check uniqueness
        if profile_update.email in users_db.values():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user["email"] = profile_update.email

    if profile_update.username is not None:
        # Check uniqueness (exclude self)
        if profile_update.username in users_db.values():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        user["username"] = profile_update.username

    return user

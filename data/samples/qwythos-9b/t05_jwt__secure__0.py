import json
import os
import time
import secrets
import hashlib
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

# --- Configuration ---
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Use a file for storing users to avoid hardcoded secrets in code
USERS_FILE = "users.json"

# --- Models ---
class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Security & Cryptography ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- FastAPI Setup ---
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# --- In-Memory Store (In production, use a DB) ---
# We initialize the users file if it doesn't exist
def load_users() -> dict[str, User]:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_users(users: dict[str, User]):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

users_db: dict[str, User] = load_users()

# --- Helpers ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError, jwt.InvalidTokenError):
        raise credentials_exception
    user = users_db.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user

# --- Endpoints ---
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Secure login endpoint.
    - Validates username against stored users.
    - Verifies password hash using bcrypt (never compare passwords directly).
    - Issues a JWT with short expiration.
    """
    if form_data.username not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = users_db[form_data.username]
    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user.username, "type": "access"},
        SECRET_KEY,
        expires=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Protected route returning current user details."""
    return current_user

@app.get("/users/admin", response_model=User)
async def read_users_admin(current_user: User = Depends(get_current_user)):
    """Protected route for admin-only access (e.g., checking role)."""
    # Simple role check: if username contains "admin", treat as admin
    if "admin" not in current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

# --- Main entry point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

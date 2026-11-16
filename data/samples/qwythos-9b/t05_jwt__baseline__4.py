# qwythos_auth.py
# JWT-based authentication for FastAPI with token-issuing login and protected routes
# Author: Qwythos (Empero AI)

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from jose import jwt, JWTError
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SECRET_KEY = "your-secret-key"  # In production, use environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(BaseModel):
    id: UUID
    email: str
    name: str

class TokenData(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str

class CreateUser(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ---------------------------------------------------------------------------
# In-memory database
# ---------------------------------------------------------------------------
users_db = {
    UUID("a1234567-89ab-cdef-0123-456789abcdef"): {
        "email": "user@example.com",
        "password": "secure_password",
        "name": "Alice"
    },
    UUID("b1234567-89ab-cdef-0123-456789abcdef"): {
        "email": "admin@example.com",
        "password": "admin_password",
        "name": "Bob"
    },
}

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = users_db.get(email)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return User(**user)

def get_current_user_me(token: str = Header(None, alias="Authorization")) -> User:
    """
    Alternative dependency that reads token from Authorization header
    (Bearer <token>) for scenarios where OAuth2PasswordBearer is not suitable.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Extract token from "Bearer <token>"
        _, _, token = token.split(" ", 2)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = users_db.get(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(**user)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="JWT Authentication Demo",
    description="Qwythos JWT-based authentication with token-issuing login and protected routes",
    version="1.0.0",
)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not users_db[user["email"]]["password"] == form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": form_data.username, "exp": datetime.now(timezone.utc) + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/items/{item_id}")
async def read_item(item_id: int, user: User = Depends(get_current_user)):
    return {"item_id": item_id, "user": user.email}

@app.post("/users")
async def create_user(user_data: CreateUser):
    if "email" in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with that email already exists",
        )
    users_db[user_data.email] = {
        "email": user_data.email,
        "password": user_data.password,
        "name": user_data.name,
    }
    return {"message": "User created"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

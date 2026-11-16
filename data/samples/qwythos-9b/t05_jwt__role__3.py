from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load this from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------
class User(BaseModel):
    username: str
    email: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ------------------------------------------------------------------
# FastAPI app setup
# ------------------------------------------------------------------
app = FastAPI(title="JWT Auth Example")

# ------------------------------------------------------------------
# In-memory user store (replace with DB in production)
# ------------------------------------------------------------------
# Format: { "username": { "email": "...", "hashed_password": "..." } }
users_db: dict[str, dict[str, str]] = {
    "admin": {
        "email": "admin@example.com",
        "hashed_password": "password"  # In production, hash this with pwdlib
    }
}

# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decode JWT and fetch user from store. Raises 401 if invalid."""
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
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Look up user in our in-memory DB
    user_dict = users_db.get(token_data.username)
    if not user_dict:
        raise credentials_exception
    return User(**user_dict)

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["email"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": form_data.username, "exp": datetime.now(timezone.utc) + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/protected", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """A protected endpoint that returns the authenticated user data."""
    return current_user

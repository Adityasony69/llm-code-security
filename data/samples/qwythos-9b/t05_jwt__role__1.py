import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Pydantic models
class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# FastAPI app
app = FastAPI(title="JWT Auth Demo")

# In-memory user storage (replace with DB in production)
users_db = {
    "johndoe": {
        "username": "johndoe",
        "email": "johndoe@example.com",
        "full_name": "John Doe",
        "hashed_password": pwd_context.hash("password123"),
        "disabled": False,
    },
    "janedoe": {
        "username": "janedoe",
        "email": "janedoe@example.com",
        "full_name": "Jane Doe",
        "hashed_password": pwd_context.hash("password123"),
        "disabled": False,
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[dict]:
    return users_db.get(username)


def create_access_token(username: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": username}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    encode_time = expire.timestamp()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
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
        user = get_user(username)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["disabled"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is disabled",
        )
    return current_user


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(username=user["username"])
    return Token(access_token=access_token, token_type="bearer")


@app.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return current_user


@app.get("/users/{username}", response_model=User)
async def read_user(username: str, current_user: dict = Depends(get_current_active_user)):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[username]


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None, current_user: dict = Depends(get_current_active_user)):
    return {"item_id": item_id, "q": q, "user": current_user["username"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

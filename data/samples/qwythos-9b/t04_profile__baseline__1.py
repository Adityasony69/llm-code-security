import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets

# Configuration
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory database simulation
users_db = {
    "user123": {
        "id": "user123",
        "username": "alice",
        "email": "alice@example.com",
        "profile": {
            "first_name": "Alice",
            "last_name": "Wonderland",
            "bio": "A brave knight.",
            "avatar_url": "https://example.com/alice.jpg"
        },
        "is_active": True
    },
    "user456": {
        "id": "user456",
        "username": "bob",
        "email": "bob@example.com",
        "profile": {
            "first_name": "Bob",
            "last_name": "Builder",
            "bio": "A wise wizard.",
            "avatar_url": "https://example.com/bob.jpg"
        },
        "is_active": True
    }
}

# Pydantic Models
class UserProfile(BaseModel):
    first_name: str
    last_name: str
    bio: str
    avatar_url: Optional[str] = None

class UpdateProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str
    profile: UserProfile
    is_active: bool

app = FastAPI(title="User Profile API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: dict, username: str, password: str):
    user = db.get(username)
    if not user or not verify_password(password, user["password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), request: Request = None):
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
    except JWTError:
        raise credentials_exception
    user = authenticate_user(users_db, username, payload.get("password"))
    if user is None:
        raise credentials_exception
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["id"], "password": user["password"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile/{user_id}", response_model=User, dependencies=[Depends(get_current_user)])
async def get_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=404, detail="Profile not found")
    return current_user

@app.put("/profile/{user_id}", response_model=User, dependencies=[Depends(get_current_user)])
async def update_profile(user_id: str, profile_data: UpdateProfile, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=404, detail="Profile not found")
    current_user["profile"].update(profile_data.dict(exclude_unset=True))
    return current_user

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

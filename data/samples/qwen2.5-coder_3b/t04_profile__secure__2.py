from fastapi import FastAPI, Depends, HTTPException, Path, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import BaseModel
import os

# FastAPI application instance
app = FastAPI()

# Secret key for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Sample user data (in a real scenario, this would be fetched from a database)
users_db = {
    "user1": {
        "username": "user1",
        "email": "user1@example.com",
        "hashed_password": pwd_context.hash("password1"),
        "profile": {
            "name": "John Doe",
            "age": 30,
            "bio": "Software engineer"
        }
    }
}

# Pydantic model for user profile
class UserProfile(BaseModel):
    name: str
    age: int
    bio: str

# Pydantic model for login request
class UserLogin(BaseModel):
    username: str
    password: str

# Function to authenticate a user
def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user:
        return False
    if not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user

# Function to create an access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Route for user login
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Route for fetching user profile
@app.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str = Path(..., regex=r"^[a-zA-Z0-9]+$"), token: str = Depends(oauth2_scheme)):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["profile"]

# Route for updating user profile
@app.put("/users/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str = Path(..., regex=r"^[a-zA-Z0-9]+$"), token: str = Depends(oauth2_scheme), profile: UserProfile = Body(...)):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["profile"].update(profile.dict())
    return user["profile"]

# Sample response model for token
class Token(BaseModel):
    access_token: str
    token_type: str

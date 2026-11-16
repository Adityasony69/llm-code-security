from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()

# Mock database
fake_users_db = {
    "john.doe": {
        "username": "john.doe",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "hashed_password": "hashed_password_123",
        "is_active": True,
        "id": 1
    },
    "jane.smith": {
        "username": "jane.smith",
        "full_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "hashed_password": "hashed_password_456",
        "is_active": True,
        "id": 2
    }
}

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Token data model
class TokenData(BaseModel):
    username: Optional[str] = None

# Dummy user data model for demonstration
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True

# Dummy user profile data model for demonstration
class UserProfile(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None

# Dummy response model
class UserProfileResponse(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None

# Dummy function to verify token
def verify_token(token: str, credentials_exception=HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

# Dummy function to get user data
def get_user_data(token: str) -> dict:
    user_data = fake_users_db.get(verify_token(token).get("username"))
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_data

# Endpoint to fetch user profile
@app.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, token: str = Depends(oauth2_scheme)):
    user_data = get_user_data(token)
    if user_id != user_data.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    return UserProfileResponse(full_name=user_data.get("full_name"), email=user_data.get("email"), bio=user_data.get("bio"))

# Endpoint to update user profile
@app.put("/users/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(user_id: int, user_profile: UserProfile, token: str = Depends(oauth2_scheme)):
    user_data = get_user_data(token)
    if user_id != user_data.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    updated_user_data = {
        **user_data,
        **user_profile.dict(exclude_unset=True)
    }

    # Update the user data in the mock database
    fake_users_db[user_data.get("username")] = updated_user_data

    return UserProfileResponse(full_name=updated_user_data.get("full_name"), email=updated_user_data.get("email"), bio=updated_user_data.get("bio"))

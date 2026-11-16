from fastapi import FastAPI, HTTPException, Depends, Request, Body
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import secrets
import uuid

app = FastAPI()

# Mock database
users_db = {
    "user1": {"id": "user1", "username": "user1", "password": "password1"},
    "user2": {"id": "user2", "username": "user2", "password": "password2"}
}

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    email: str
    bio: str

def verify_password(plain_password, hashed_password):
    # This is a placeholder for password verification logic
    return True

def get_user_data(token: str = Depends(oauth2_scheme)):
    # This is a placeholder for user data retrieval logic
    if token == "your_secret_token":
        return {"user_id": "user1"}
    raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = secrets.token_urlsafe(32)
    user_data = get_user_data(access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str, user_data: dict = Depends(get_user_data)):
    if user_id != user_data["user_id"]:
        raise HTTPException(status_code=403, detail="Access forbidden")

    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(username=user["username"], email="example@example.com", bio="This is a bio.")

@app.put("/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, user_data: dict = Depends(get_user_data), profile_data: UserProfile = Body(...)):
    if user_id != user_data["user_id"]:
        raise HTTPException(status_code=403, detail="Access forbidden")

    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user profile fields
    user["username"] = profile_data.username
    user["email"] = profile_data.email
    user["bio"] = profile_data.bio

    return UserProfile(username=user["username"], email=user["email"], bio=user["bio"])

class Token(BaseModel):
    access_token: str
    token_type: str

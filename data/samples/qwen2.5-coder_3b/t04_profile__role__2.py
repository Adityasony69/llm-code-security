from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional

# Example user data (in a real-world application, this would be fetched from a database)
users = {
    1: {
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
        "profile": {
            "name": "Alice Johnson",
            "age": 30,
            "bio": "Software developer"
        }
    },
    2: {
        "username": "bob",
        "email": "bob@example.com",
        "password": "password456",
        "profile": {
            "name": "Bob Smith",
            "age": 25,
            "bio": "Data analyst"
        }
    }
}

# OAuth2PasswordBearer is a class from FastAPI that handles authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str
    profile: dict

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None

app = FastAPI()

# Dummy token (in a real-world application, this would be obtained from a token store)
fake_token = "fake-super-secret-token"

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or form_data.password != "secret":
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": fake_token, "token_type": "bearer"}

@app.get("/users/{user_id}")
async def read_user(user_id: int = Query(...), token: str = Depends(oauth2_scheme)):
    if token != fake_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]

@app.put("/users/{user_id}")
async def update_user(user_id: int = Query(...), token: str = Depends(oauth2_scheme), update: UserProfileUpdate = Body(...)):
    if token != fake_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user profile
    for key, value in update.dict(exclude_unset=True).items():
        users[user_id]["profile"][key] = value
    
    return users[user_id]

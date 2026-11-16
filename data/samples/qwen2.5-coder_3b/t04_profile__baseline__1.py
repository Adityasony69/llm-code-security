from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Simulated in-memory database
users = {
    "1": {"username": "alice", "email": "alice@example.com", "age": 30},
    "2": {"username": "bob", "email": "bob@example.com", "age": 25},
}

# OAuth2PasswordBearer instance for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str
    age: int

class UpdateUser(BaseModel):
    username: str = None
    email: str = None
    age: int = None

def get_user(token: str = Depends(oauth2_scheme)):
    # This function would typically check the token against a database
    # For simplicity, we assume the token is a user ID
    user_id = token
    if user_id not in users:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return users[user_id]

@app.get("/user/{user_id}", response_model=User)
async def read_user(user_id: str = Query(..., description="User ID to retrieve")),
                  user: User = Depends(get_user)):
    return users[user_id]

@app.put("/user/{user_id}", response_model=User)
async def update_user(
    user_id: str = Query(..., description="User ID to update"),
    user_update: UpdateUser = Body(...),
    user: User = Depends(get_user)
):
    if user_update.username:
        users[user_id]["username"] = user_update.username
    if user_update.email:
        users[user_id]["email"] = user_update.email
    if user_update.age:
        users[user_id]["age"] = user_update.age

    return users[user_id]

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_id = form_data.username
    if user_id not in users:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": user_id, "token_type": "bearer"}

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
import jwt
import os

app = FastAPI()

# Dummy database simulation
users = {
    "alice": {"password": "password123"},
    "bob": {"password": "password456"}
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

class UserProfile(BaseModel):
    name: str
    email: str

def verify_password(plain_password, hashed_password):
    # For simplicity, just checking against a hardcoded dictionary
    return hashed_password == plain_password

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user = users.get(user_id)
        if user is None:
            raise credentials_exception
        return user
    except jwt.ExpiredSignatureError:
        raise credentials_exception

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = jwt.encode({"sub": str(user["id"])}, os.getenv("SECRET_KEY"), algorithm="HS256")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/{user_id}")
async def read_user(user_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}")
async def update_user(user_id: int, user_profile: UserProfile, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = user_profile.name
    user.email = user_profile.email
    db.commit()
    db.refresh(user)
    return user

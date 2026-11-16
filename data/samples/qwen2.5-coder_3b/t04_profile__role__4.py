from fastapi import FastAPI, HTTPException, Depends, Query, Body, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# Define the database model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile = Column(String, nullable=True)

# Create an asynchronous database engine
DATABASE_URL = "sqlite:///your_database.db"
engine = create_async_engine(DATABASE_URL)
async_session = AsyncSession(engine)

# Define FastAPI app
app = FastAPI()

# OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Function to authenticate a user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # This would typically involve checking the token in a database or other storage
    # For simplicity, we'll just return a dummy user
    user = {"id": 1, "username": "testuser"}
    return user

# Function to handle user profile update
async def update_user_profile(user: UserUpdate, current_user: User):
    async with async_session.begin() as session:
        stmt = update(User).where(User.id == current_user.id).values(
            profile=user.profile
        )
        await session.execute(stmt)
        await session.commit()
        return {"message": "Profile updated successfully"}

# Define user profile update model
class UserUpdate(BaseModel):
    profile: str = Field(..., description="User profile information")

# Define the main endpoint
@app.post("/profile/{user_id}")
async def update_profile(
    user_id: int,
    user: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="User not authorized to update profile")

    try:
        return await update_user_profile(user, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

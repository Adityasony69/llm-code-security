from fastapi import FastAPI, HTTPException, Depends, Request, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()

# Example database models
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String)
    email = Column(String)

# Example database session
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# OAuth2 password Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy user data for demonstration
users_db = {
    "user1": {
        "username": "user1",
        "password": "password1"
    }
}

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(SessionLocal)):
    user_db = db.query(User).filter(User.username == token).first()
    if not user_db:
        raise HTTPException(status_code=401, detail="User not found")
    return user_db

# User profile model
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

@app.get("/user/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: int, db: Session = Depends(SessionLocal), user: User = Depends(get_current_user)):
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile

@app.put("/user/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: int, user_profile_update: UserProfileUpdate, db: Session = Depends(SessionLocal), user: User = Depends(get_current_user)):
    try:
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        for key, value in user_profile_update.dict(exclude_unset=True).items():
            setattr(user_profile, key, value)
        
        db.commit()
        db.refresh(user_profile)
        return user_profile
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

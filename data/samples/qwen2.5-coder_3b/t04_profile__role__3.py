from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_db, User, UserProfile

app = FastAPI()

# OAuth2PasswordBearer requires a token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Example User model for demonstration
class User(BaseModel):
    id: int
    username: str
    email: str

# Example UserProfile model for demonstration
class UserProfile(BaseModel):
    id: int
    user_id: int
    bio: str = None
    profile_picture_url: str = None

# Mock database to simulate user data
users = [
    User(id=1, username="john_doe", email="john@example.com"),
    User(id=2, username="jane_doe", email="jane@example.com"),
]

# Mock database to simulate user profiles
user_profiles = [
    UserProfile(id=1, user_id=1, bio="I am John Doe", profile_picture_url="https://example.com/johndoe.jpg"),
    UserProfile(id=2, user_id=2, bio="I am Jane Doe", profile_picture_url="https://example.com/janedoe.jpg"),
]

# Function to authenticate user
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.verify_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

# Token retrieval function (for demonstration purposes)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return authenticate_user(token, "password", get_db())

# Endpoint to fetch user profile by user ID
@app.get("/users/{user_id}/profile", response_model=UserProfile)
def get_user_profile(user_id: int, current_user: User = Depends(get_current_user)):
    user_profile = next((up for up in user_profiles if up.user_id == user_id), None)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile

# Endpoint to update user profile by user ID
@app.put("/users/{user_id}/profile", response_model=UserProfile)
def update_user_profile(user_id: int, user_profile_update: UserProfile, current_user: User = Depends(get_current_user)):
    user_profile = next((up for up in user_profiles if up.user_id == user_id), None)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Update user profile fields
    user_profile.bio = user_profile_update.bio
    user_profile.profile_picture_url = user_profile_update.profile_picture_url
    
    # Save the updated user profile
    db = get_db()
    db.add(user_profile)
    db.commit()
    db.refresh(user_profile)
    
    return user_profile

# Database setup and initialization (for demonstration purposes)
def create_engine():
    # This is a placeholder for a real database connection
    return

def get_db():
    # This is a placeholder for a real database session
    return

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

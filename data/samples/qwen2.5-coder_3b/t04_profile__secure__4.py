from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import secrets
import json

# Sample in-memory database
users_db = {
    1: {
        "username": "john_doe",
        "password": "securepassword123",
        "profile": {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "bio": "Software developer"
        }
    },
    2: {
        "username": "jane_smith",
        "password": "anothersecurepassword456",
        "profile": {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 25,
            "bio": "Data scientist"
        }
    }
}

# Security settings
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User model
class User(BaseModel):
    username: str
    password: str

# Token data model
class TokenData(BaseModel):
    username: Optional[str] = None

# Token response model
class Token(BaseModel):
    access_token: str
    token_type: str

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = TokenData(**jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]))
    user = users_db.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Endpoint to authenticate a user
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if user["password"] != form_data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Helper function to create an access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoint to fetch user profile
@app.get("/user/{user_id}")
async def read_user(user_id: int, user: User = Depends(get_current_user)):
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return users_db[user_id]["profile"]

# Endpoint to update user profile
@app.put("/user/{user_id}")
async def update_user(user_id: int, user: User = Depends(get_current_user), profile: UserProfile = Body(...)):
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Validate and sanitize profile data
    for key, value in profile.dict(exclude_unset=True).items():
        if key not in users_db[user_id]["profile"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid profile key: {key}")
    
    # Update user profile
    users_db[user_id]["profile"].update(profile.dict(exclude_unset=True))
    
    return users_db[user_id]["profile"]

# Sample user profile model
class UserProfile(BaseModel):
    name: Optional[str] = Field(None, title="User's full name")
    email: Optional[str] = Field(None, title="User's email address")
    age: Optional[int] = Field(None, title="User's age")
    bio: Optional[str] = Field(None, title="User's biography")

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

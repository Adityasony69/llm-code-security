from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# OAuth2PasswordBearer is used for JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Sample user database
users_db = {
    "user1": {
        "username": "user1",
        "password": "password1",
        "email": "user1@example.com",
        "profile": {
            "name": "John Doe",
            "age": 30,
            "address": "123 Main St"
        }
    }
}

# User model
class User(BaseModel):
    username: str
    email: str
    profile: dict

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Token data
fake_secret_key = "super-secret-key"
algorithm = "HS256"
access_token_expires = timedelta(minutes=30)

# Dummy token generator
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, fake_secret_key, algorithm=algorithm)
    return encoded_jwt

# Dummy authentication function
def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Dummy token creation function
def create_token(data: dict):
    access_token = create_access_token(data)
    return {"access_token": access_token, "token_type": "bearer"}

# OAuth2PasswordBearer is used for JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define the User model
class User(BaseModel):
    username: str
    email: str
    profile: dict

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Route to authenticate and return a token
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Route to fetch a user profile by user ID
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = users_db.get(user_id)
    if user is None:
        raise credentials_exception
    return user

# Route to update a user profile by user ID
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: User, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = users_db.get(user_id)
    if user is None:
        raise credentials_exception

    # Update the user's profile with the provided data
    user["profile"] = user["profile"].update(user.profile)

    # Return the updated user profile
    return user

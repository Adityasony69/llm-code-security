from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI()

# Security configurations
SECRET_KEY = "your-secret-key"  # Change this to a strong secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy users (in a real app, this would be loaded from a database)
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "password": pwd_context.hash("johndoe123"),
    },
    "alice": {
        "username": "alice",
        "password": pwd_context.hash("alice123"),
    },
}

# Function to authenticate user
def authenticate_user(username: str, password: str) -> Optional[str]:
    user = fake_users_db.get(username)
    if user and pwd_context.verify(password, user["password"]):
        return user["username"]
    return None

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoint to login and receive a token
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = authenticate_user(form_data.username, form_data.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route that requires a valid JWT token
@app.get("/protected", response_model=User)
async def read_protected_route(current_user: User = Depends(oauth2_scheme)):
    return {"username": current_user.username}

# User model for response
class User(BaseModel):
    username: str

# Token model for response
class Token(BaseModel):
    access_token: str
    token_type: str

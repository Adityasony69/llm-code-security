from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import secrets

app = FastAPI()

# Security settings
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
SALT = secrets.token_hex(16)
KDF_ALGORITHM = hashes.SHA256()
KDF_ITERATIONS = 100000

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str = None

# User model
class User(BaseModel):
    username: str
    password: str

# User database
users_db = {}

# Generate a new RSA key pair
def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Hash a password
def hash_password(password):
    kdf = PBKDF2HMAC(
        algorithm=KDF_ALGORITHM,
        length=32,
        salt=SALT.encode(),
        iterations=KDF_ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# Verify a password
def verify_password(plain_password, hashed_password):
    kdf = PBKDF2HMAC(
        algorithm=KDF_ALGORITHM,
        length=32,
        salt=SALT.encode(),
        iterations=KDF_ITERATIONS,
        backend=default_backend()
    )
    return kdf.verify(plain_password.encode(), hashed_password)

# Create a new user
@app.post("/register", response_model=User)
async def create_user(user: User):
    hashed_password = hash_password(user.password)
    user_db[user.username] = {
        "hashed_password": hashed_password,
        "public_key": private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    }
    return user

# Login endpoint
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_db_entry = users_db.get(form_data.username)
    if not user_db_entry or not verify_password(form_data.password, user_db_entry["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Token creation
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Protected route
@app.get("/protected", dependencies=[Depends(oauth2_scheme)])
async def protected_route(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_db_entry = users_db.get(username)
    if user_db_entry is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    return {"username": username, "public_key": user_db_entry["public_key"]}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

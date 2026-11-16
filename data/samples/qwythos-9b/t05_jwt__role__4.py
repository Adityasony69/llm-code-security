from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Session, create_engine, select
import uvicorn

# --- Security Configuration ---
SECRET_KEY = "your-secret-key-here"  # In production, use environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Models ---
class User(SQLModel, table=True):
    id: Optional[int] = None
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    # Add other fields if needed (e.g., scope)

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./security_demo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = SessionLocal

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- JWT Handling ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- FastAPI App ---
app = FastAPI(title="JWT Auth Demo")

# Seed initial user
@app.on_event("startup")
async def startup_event():
    with Session(engine) as session:
        stmt = select(User).where(User.email == "user@example.com")
        if not session.exec(stmt).first():
            hashed_pw = get_password_hash("password123")
            session.add(User(
                email="user@example.com",
                username="user",
                hashed_password=hashed_pw
            ))
            session.commit()

# --- Endpoints ---
@app.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await request.state.db.get(User, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")

@app.get("/protected", dependencies=[Depends(oauth2_scheme)])
async def read_secure(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"Hello": f"User {username}"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        uvicorn.run(app, host="0.0.0.0", port=8000)

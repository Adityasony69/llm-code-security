from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select

# FastAPI application setup
app = FastAPI()

# Database configuration
DATABASE_URL = "sqlite:///users.db"
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model definition
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    # Add other fields as needed

# Dependency to get the current user
def get_current_user(db: AsyncSession = Depends(SessionLocal)):
    # Simulate user authentication here
    # In a real application, this would involve checking tokens or session data
    current_user = User(id=1, username="example_user", email="example@example.com")
    return current_user

# Endpoint to fetch a user profile
@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        query = select(User).where(User.id == user_id)
        user = await db.execute(query)
        user = user.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

# Endpoint to update a user profile
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: User, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        query = select(User).where(User.id == user_id)
        user = await db.execute(query)
        user = user.scalar()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user fields
        user.username = user.username or user.username
        user.email = user.email or user.email
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user

# Example usage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

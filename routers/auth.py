from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import UserCreate
from security import hash_password

router = APIRouter(
    prefix = "/auth",
    tags = ["Authentication"]
)

@router.post("/signup")
async def signup(user: UserCreate , db : AsyncSession =  Depends(get_db)):
    query = select(User).where(user.email == User.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    hashed_password = hash_password(user.password)
    new_user = User(
         email=user.email,
         hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User created successfully"}


    

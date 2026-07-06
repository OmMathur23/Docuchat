from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import UserCreate, UserLogin
from security import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix = "/auth",
    tags = ["Authentication"]
)

@router.post("/signup")
async def signup(user: UserCreate , db : AsyncSession =  Depends(get_db)):
    query = select(User).where(User.email == user.email)
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


@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db))->dict:
    query = select(User).where(User.email == user.email)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code= 401,
            detail = "Incorrect Email or Password"
        )
    if(verify_password(user.password, db_user.hashed_password)):
        '''
        Password correct
        │
        ▼
        Create JWT containing user_id
        │
        ▼
        Return JWT to frontend
        The frontend stores that token (usually in an HttpOnly cookie or another secure mechanism), and sends it with future requests.
        '''
        access_token = create_access_token(data = {
            "sub" : str(db_user.id) #sub: standard JWT claim meaning Subject
                                    #str? JWT Convention, just passing the integer user id also works fine
        })

    else:
        raise HTTPException(
            status_code=401,
            detail = "Incorrect Email or Password"
        )
    
    return {
        "access_token" : access_token,
        "token_type" : "bearer"
    }
    

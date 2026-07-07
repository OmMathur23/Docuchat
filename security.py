from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime, UTC
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) #int because os.getenv always returns a string but timedelta expects int
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto") #creating an object of class CryptoContext with encrypting algo = bcrpyt (widely used and reliable algorithm)

#creating an OAuth2PasswordBearer class object, helps pick 
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl= "/auth/login"  #the endpoint which assigns the token
)
'''
This object knows how to Look for the Authorization header and check that it starts with Bearer. 

Extracts the token.
Returns it.
Raises a 401 Unauthorized automatically if the header is missing or malformed.

You don't call any methods yourself though.
'''

async def get_current_user(token = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)): #before entering the function, get JWT Token and a Database session       
        '''
    Receive Request
            │
            ▼
    Extract JWT (oauth2_scheme)
            │
            ▼
    Decode JWT
            │
            ▼
    Read "sub"
            │
            ▼
    Query User table
            │
            ▼
    Return User object
    ''' 
        try:
            payload =jwt.decode(
                    token,
                    SECRET_KEY,
                    algorithms= ALGORITHM     
                ) #we only care about payload["sub"] because that's where our user id is, we dont care about payload["expire"]
            user_id = payload.get("sub")
  #why .get() instead of  ["sub"]? Because of sub is malformed->empty, ["sub"] gives key error while .get gives us None which we can handle ourselves
            if user_id is None:
                raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
        except JWTError:
             raise HTTPException(
                  status_code = 401,
                  detail= "Could not validate credentials"
             )
        #put in try catch in case token has expired or something
        query = select(User).where(User.id == int(user_id))
        res = await db.execute(query)
        db_user = res.scalar_one_or_none() #return at most 1 row, if more -> raise if 0 return none
        if db_user is None:
            raise HTTPException(
                status_code= 401,
                detail = "Could not validate credentials"
            )
        return db_user
def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password: str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data: dict)->str:
    to_encode = data.copy() #creates a new dictionary to_encode which points to a different memory location than data
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
    to_encode, #payload
    SECRET_KEY,
    algorithm=ALGORITHM
    )
    return encoded_jwt                                      


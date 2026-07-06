from passlib.context import CryptContext
from jose import jwt
from datetime import timedelta, datetime, UTC
from dotenv import load_dotenv
import os

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) #int because os.getenv always returns a string but timedelta expects int
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto") #creating an object of class CryptoContext with encrypting algo = bcrpyt (widely used and reliable algorithm)

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password: str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data: dict)->str:
    to_encode = data.copy() #creates a new dictionary to_encode which points to a different memory location than data
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
    to_encode,
    SECRET_KEY,
    algorithm=ALGORITHM
    )
    return encoded_jwt                                      


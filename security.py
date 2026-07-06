from passlib.context import CryptContext

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto") #creating an object of class CryptoContext with encrypting algo = bcrpyt (widely used and reliable algorithm)

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password: str)->bool:
    return pwd_context.verify(plain_password,hashed_password)
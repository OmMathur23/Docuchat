from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    email : EmailStr
    password : str

class UserLogin(BaseModel):
    email : EmailStr
    password : str

class DocumentCreate(BaseModel):
    title: str
    content: str

class AskRequest(BaseModel):
    question : str
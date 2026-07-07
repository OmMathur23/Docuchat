from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    email : EmailStr
    password : str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")
        return v

class UserLogin(BaseModel):
    email : EmailStr
    password : str

class DocumentCreate(BaseModel):
    title: str
    content: str
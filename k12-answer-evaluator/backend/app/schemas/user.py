from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    grade: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    grade: Optional[str] = None
    
    class Config:
        from_attributes = True

class UpdateProfile(BaseModel):
    full_name: Optional[str] = None
    grade: Optional[str] = None


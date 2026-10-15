from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72, description="Password must be between 6 and 72 characters")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    role: Optional[UserRole] = UserRole.REQUESTER

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v):
        if isinstance(v, str):
            cleaned = v.strip().upper()
            for r in UserRole:
                if r.value == cleaned or r.name == cleaned:
                    return r
            if cleaned in ["USER", "CUSTOMER"]:
                return UserRole.PASSENGER
            if cleaned in ["SUPPORT", "STAFF", "AGENT"]:
                return UserRole.SUPPORT_AGENT
            if cleaned in ["ENGINEER", "TECH"]:
                return UserRole.SUPPORT_ENGINEER
            if cleaned in ["ADMINISTRATOR", "OPS"]:
                return UserRole.ADMIN
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

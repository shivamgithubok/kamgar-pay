from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=150)
    organization_code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    organization_code: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

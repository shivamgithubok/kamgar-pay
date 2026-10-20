from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role_code: str = Field(default="staff", min_length=2, max_length=50)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str]
    status: str
    is_locked: bool
    last_login_at: Optional[datetime]
    role_codes: list[str]
    created_at: datetime
    updated_at: datetime

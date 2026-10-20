from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from src.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except ValueError:
        return pwd_context.hash(password, scheme="pbkdf2_sha256")


def create_access_token(*, subject: str, organization_id: str, roles: list[str]) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "org_id": organization_id,
        "roles": roles,
        "exp": expires_at,
    }
    encoded_jwt = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt, settings.access_token_expire_minutes * 60


def normalize_code(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "organization"

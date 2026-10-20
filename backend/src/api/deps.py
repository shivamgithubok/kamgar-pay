from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.core.config import settings
from src.database.models import User
from src.db.session import get_db
from src.services.users import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        organization_id = payload.get("org_id")
        if not user_id or not organization_id:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = get_user_by_id(db, organization_id=organization_id, user_id=user_id)
    if user is None or user.status != "active" or user.is_locked:
        raise credentials_exception

    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        role_codes = {assignment.role.code for assignment in current_user.roles if assignment.role is not None}
        if not role_codes.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency

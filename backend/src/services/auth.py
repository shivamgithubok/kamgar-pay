from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.security import create_access_token, get_password_hash, normalize_code, verify_password
from src.database.models import Organization, Role, User, UserRole
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from src.services.users import get_user_by_email, get_user_by_id, to_user_response


DEFAULT_ROLES: dict[str, str] = {
    "organization_admin": "Organization administrator with full access to user management.",
    "staff": "Standard back-office user.",
}


def ensure_default_roles(db: Session, *, organization_id: str) -> dict[str, Role]:
    query = select(Role).where(Role.organization_id == organization_id)
    existing_roles = {role.code: role for role in db.execute(query).scalars().all()}

    for code, description in DEFAULT_ROLES.items():
        if code in existing_roles:
            continue
        role = Role(
            organization_id=organization_id,
            name=code.replace("_", " ").title(),
            code=code,
            description=description,
            is_system=False,
        )
        db.add(role)
        db.flush()
        existing_roles[code] = role

    return existing_roles


def register_organization_admin(db: Session, payload: RegisterRequest) -> User:
    organization_code = normalize_code(payload.organization_code or payload.organization_name)

    organization = Organization(
        name=payload.organization_name.strip(),
        code=organization_code,
        status="active",
    )
    db.add(organization)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization code already exists",
        ) from exc

    try:
        roles = ensure_default_roles(db, organization_id=organization.id)

        user = User(
            organization_id=organization.id,
            full_name=payload.full_name.strip(),
            email=payload.email.lower(),
            phone=payload.phone,
            password_hash=get_password_hash(payload.password),
            status="active",
        )
        db.add(user)
        db.flush()

        db.add(UserRole(user_id=user.id, role_id=roles["organization_admin"].id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed because a unique field already exists",
        ) from exc

    created_user = get_user_by_id(db, organization_id=organization.id, user_id=user.id, required=True)
    return created_user


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    organization_code = normalize_code(payload.organization_code)

    organization = db.execute(
        select(Organization).where(Organization.code == organization_code, Organization.status == "active")
    ).scalar_one_or_none()
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user = get_user_by_email(db, organization_id=organization.id, email=payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.status != "active" or user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not available",
        )

    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()

    authenticated_user = get_user_by_id(db, organization_id=user.organization_id, user_id=user.id, required=True)
    return authenticated_user


def build_token_response(user: User) -> TokenResponse:
    role_codes = sorted({assignment.role.code for assignment in user.roles if assignment.role is not None})
    access_token, expires_in = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
        roles=role_codes,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=to_user_response(user),
    )

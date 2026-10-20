from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.core.security import get_password_hash
from src.database.models import Role, User, UserRole
from src.schemas.user import UserCreateRequest, UserResponse


def base_user_query() -> Select[tuple[User]]:
    return select(User).options(selectinload(User.roles).selectinload(UserRole.role))


def get_user_by_id(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    required: bool = False,
) -> User | None:
    query = base_user_query().where(
        User.organization_id == organization_id,
        User.id == user_id,
    )
    user = db.execute(query).scalar_one_or_none()
    if user is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_user_by_email(db: Session, *, organization_id: str, email: str) -> User | None:
    query = base_user_query().where(
        User.organization_id == organization_id,
        User.email == email.lower(),
    )
    return db.execute(query).scalar_one_or_none()


def list_users(db: Session, *, organization_id: str) -> list[User]:
    query = base_user_query().where(User.organization_id == organization_id).order_by(User.full_name.asc())
    return list(db.execute(query).scalars().all())


def get_role_by_code(db: Session, *, organization_id: str, role_code: str) -> Role | None:
    query = select(Role).where(Role.organization_id == organization_id, Role.code == role_code)
    return db.execute(query).scalar_one_or_none()


def create_user(db: Session, *, organization_id: str, payload: UserCreateRequest) -> User:
    existing_user = get_user_by_email(db, organization_id=organization_id, email=payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists in the organization",
        )

    role = get_role_by_code(db, organization_id=organization_id, role_code=payload.role_code)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    user = User(
        organization_id=organization_id,
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
        status="active",
    )
    try:
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User could not be created because a unique field already exists",
        ) from exc

    created_user = get_user_by_id(db, organization_id=organization_id, user_id=user.id, required=True)
    return created_user


def to_user_response(user: User) -> UserResponse:
    role_codes = sorted({assignment.role.code for assignment in user.roles if assignment.role is not None})
    return UserResponse(
        id=user.id,
        organization_id=user.organization_id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=user.status,
        is_locked=user.is_locked,
        last_login_at=user.last_login_at,
        role_codes=role_codes,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

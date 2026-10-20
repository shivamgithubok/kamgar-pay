from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.user import UserCreateRequest, UserResponse
from src.services.users import create_user, get_user_by_id, list_users, to_user_response


router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)


@router.get("/", response_model=list[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin")),
) -> list[UserResponse]:
    users = list_users(db, organization_id=current_user.organization_id)
    return [to_user_response(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin")),
) -> UserResponse:
    user = get_user_by_id(db, organization_id=current_user.organization_id, user_id=user_id, required=True)
    return to_user_response(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_organization_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin")),
) -> UserResponse:
    user = create_user(db, organization_id=current_user.organization_id, payload=payload)
    return to_user_response(user)

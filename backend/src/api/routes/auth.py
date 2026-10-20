from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from src.services.auth import authenticate_user, build_token_response, register_organization_admin


router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = register_organization_admin(db, payload)
    return build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload)
    return build_token_response(user)

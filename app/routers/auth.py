from fastapi import APIRouter, Depends, status

from app.database.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db=Depends(get_db)) -> RegisterResponse:
    return AuthService(db).register(payload)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db=Depends(get_db)) -> LoginResponse:
    return AuthService(db).login(payload.email, payload.password, payload.store_name)

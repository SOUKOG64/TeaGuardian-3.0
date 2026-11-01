from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import Credentials, RefreshIn, TokenPair, UserOut
from ..services import auth as service
from .deps import current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=201, summary="Регистрация")
def register(data: Credentials, db: Session = Depends(get_db)):
    return service.register(db, data.username, data.password)


@router.post("/login", response_model=TokenPair, summary="Вход")
def login(data: Credentials, db: Session = Depends(get_db)):
    return service.login(db, data.username, data.password)


@router.post("/refresh", response_model=TokenPair, summary="Обновить токены")
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    return service.refresh(db, data.refresh_token)


@router.post("/logout", status_code=204, summary="Выход")
def logout(data: RefreshIn, db: Session = Depends(get_db)):
    service.logout(db, data.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserOut, summary="Кто я")
def me(user: User = Depends(current_user)):
    return service.profile(user)

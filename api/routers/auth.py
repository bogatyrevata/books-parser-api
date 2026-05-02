from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import User
from api.dependencies import get_db
from api.schemas import UserCreate, UserSchema, TokenSchema
from api.auth import hash_password, verify_password, create_access_token, get_current_user, create_refresh_token, RefreshToken
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime

auth_router = APIRouter(
    prefix="/auth",  # все роуты начинаются с /auth
    tags=["auth"]    # группировка в Swagger
)

# регистрация нового пользователя. Первый пользователь становится админом, остальные — обычными пользователями

@auth_router.post("/register", response_model=UserSchema, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # проверяем что такого пользователя нет
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    # первый пользователь становится админом
    is_first = db.query(User).count() == 0

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        is_admin=is_first
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/login", response_model=TokenSchema)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token(user.id, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@auth_router.post("/refresh", response_model=TokenSchema)
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    # ищем токен в базе
    token_obj = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

    if not token_obj:
        raise HTTPException(status_code=401, detail="Невалидный refresh токен")

    if token_obj.expires_at < datetime.utcnow():
        db.delete(token_obj)
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh токен истёк")

    # создаём новые токены
    user = token_obj.user
    new_access_token = create_access_token({"sub": user.username})
    new_refresh_token = create_refresh_token(user.id, db)

    # удаляем старый refresh токен
    db.delete(token_obj)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@auth_router.post("/logout", status_code=204)
def logout(refresh_token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token_obj = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if token_obj:
        db.delete(token_obj)
        db.commit()


@auth_router.get("/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

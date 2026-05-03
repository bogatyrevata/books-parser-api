from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import User, RefreshToken
from api.dependencies import get_db
from api.schemas import UserCreate, UserSchema, TokenSchema
from api.auth import hash_password, verify_password, create_access_token, get_current_user, create_refresh_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@auth_router.post("/register", response_model=UserSchema, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    result = await db.execute(select(User))
    is_first = len(result.scalars().all()) == 0

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        is_admin=is_first
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@auth_router.post("/login", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    access_token = create_access_token({"sub": user.username})
    refresh_token = await create_refresh_token(user.id, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@auth_router.post("/refresh", response_model=TokenSchema)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    token_obj = result.scalar_one_or_none()

    if not token_obj:
        raise HTTPException(status_code=401, detail="Невалидный refresh токен")

    if token_obj.expires_at < datetime.utcnow():
        await db.delete(token_obj)
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh токен истёк")

    # загружаем пользователя отдельным запросом
    result = await db.execute(select(User).where(User.id == token_obj.user_id))
    user = result.scalar_one_or_none()

    new_access_token = create_access_token({"sub": user.username})
    new_refresh_token = await create_refresh_token(user.id, db)

    await db.delete(token_obj)
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@auth_router.post("/logout", status_code=204)
async def logout(refresh_token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    token_obj = result.scalar_one_or_none()
    if token_obj:
        await db.delete(token_obj)
        await db.commit()

@auth_router.get("/me", response_model=UserSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_auth
from app.core.security import create_access_token
from app.models import User
from app.schemas.auth import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyOut,
    ApiKeyToggle,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await auth_service.get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким именем уже существует",
        )
    return await auth_service.create_user(db, payload.username, payload.password, payload.email)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        expires_in=settings.jwt_expires_minutes * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(require_auth)):
    return user


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    key, raw = await auth_service.create_api_key(db, user, payload.name)
    return ApiKeyCreated(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        key=raw,
    )


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.list_api_keys(db, user)


@router.patch("/api-keys/{key_id}", response_model=ApiKeyOut)
async def toggle_api_key(
    key_id: int,
    payload: ApiKeyToggle,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    key = await auth_service.get_api_key(db, key_id)
    if not key or key.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ключ не найден")
    return await auth_service.set_api_key_active(db, key, payload.is_active)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    key = await auth_service.get_api_key(db, key_id)
    if not key or key.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ключ не найден")
    await auth_service.revoke_api_key(db, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

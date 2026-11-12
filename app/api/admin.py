from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.security import ROLE_ADMIN, ROLE_USER
from app.models import ApiKey, User
from app.schemas.auth import ApiKeyAdminOut
from app.schemas.user import UserAdminUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    return list((await db.execute(select(User).order_by(User.id))).scalars())


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if payload.role is not None:
        if payload.role not in (ROLE_ADMIN, ROLE_USER):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Недопустимая роль"
            )
        if user.id == admin_user.id and payload.role != ROLE_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя понизить собственную роль администратора",
            )
        user.role = payload.role
    if payload.is_active is not None:
        if user.id == admin_user.id and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя деактивировать собственный аккаунт",
            )
        user.is_active = payload.is_active
    if payload.request_limit is not None:
        user.request_limit = payload.request_limit

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить собственный аккаунт"
        )
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    await db.delete(user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api-keys", response_model=list[ApiKeyAdminOut])
async def list_all_keys(
    user_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    query = select(ApiKey)
    if user_id is not None:
        query = query.where(ApiKey.user_id == user_id)
    return list((await db.execute(query.order_by(ApiKey.id))).scalars())


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_any_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    key = await db.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ключ не найден")
    await db.delete(key)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

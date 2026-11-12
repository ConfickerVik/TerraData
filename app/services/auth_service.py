"""Бизнес-логика аутентификации и управления пользователями/ключами."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    ROLE_ADMIN,
    ROLE_USER,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.models import ApiKey, User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    return (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def create_user(
    db: AsyncSession,
    username: str,
    password: str,
    email: str | None = None,
    role: str = ROLE_USER,
    request_limit: int | None = None,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        request_limit=request_limit,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    user = await get_user_by_username(db, username)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


async def create_api_key(db: AsyncSession, user: User, name: str) -> tuple[ApiKey, str]:
    raw, prefix, key_hash = generate_api_key()
    key = ApiKey(user_id=user.id, name=name, key_hash=key_hash, key_prefix=prefix)
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return key, raw


async def list_api_keys(db: AsyncSession, user: User) -> list[ApiKey]:
    return list(
        (
            await db.execute(
                select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.id)
            )
        ).scalars()
    )


async def get_api_key(db: AsyncSession, key_id: int) -> ApiKey | None:
    return await db.get(ApiKey, key_id)


async def set_api_key_active(db: AsyncSession, key: ApiKey, is_active: bool) -> ApiKey:
    key.is_active = is_active
    await db.commit()
    await db.refresh(key)
    return key


async def revoke_api_key(db: AsyncSession, key: ApiKey) -> None:
    await db.delete(key)
    await db.commit()


async def ensure_admin_user(db: AsyncSession) -> None:
    """Идемпотентно создаёт администратора из настроек (если задан пароль)."""
    if not settings.admin_password:
        return
    existing = await get_user_by_username(db, settings.admin_username)
    if existing:
        return
    await create_user(
        db,
        settings.admin_username,
        settings.admin_password,
        settings.admin_email or None,
        role=ROLE_ADMIN,
    )

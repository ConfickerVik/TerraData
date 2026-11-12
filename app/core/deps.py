"""FastAPI-зависимости аутентификации, авторизации и квот."""
from datetime import date, datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import ROLE_ADMIN, decode_access_token, hash_api_key
from app.models import ApiKey, UsageRecord, User

bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Требуется авторизация",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _user_by_api_key(db: AsyncSession, raw_key: str | None) -> User | None:
    if not raw_key:
        return None
    key = (
        await db.execute(select(ApiKey).where(ApiKey.key_hash == hash_api_key(raw_key)))
    ).scalar_one_or_none()
    if not key or not key.is_active:
        return None
    user = await db.get(User, key.user_id)
    if not user or not user.is_active:
        return None
    key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return user


async def _user_by_jwt(db: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    api_key: str | None = Depends(api_key_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Резолвит пользователя по API-ключу (приоритет) или JWT."""
    if api_key:
        user = await _user_by_api_key(db, api_key)
        if user:
            return user
    if bearer is not None:
        user = await _user_by_jwt(db, bearer.credentials)
        if user:
            return user
    raise _credentials_exc


async def _enforce_quota(db: AsyncSession, user: User) -> None:
    if user.role == ROLE_ADMIN:
        return
    limit = user.request_limit if user.request_limit is not None else settings.default_daily_quota
    today = date.today()
    record = (
        await db.execute(
            select(UsageRecord).where(
                UsageRecord.user_id == user.id, UsageRecord.date == today
            )
        )
    ).scalar_one_or_none()
    if record is None:
        db.add(UsageRecord(user_id=user.id, date=today, count=1))
        await db.commit()
        return
    if record.count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен суточный лимит запросов",
        )
    record.count += 1
    await db.commit()


async def require_auth(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    await _enforce_quota(db, user)
    return user


async def require_admin(user: User = Depends(require_auth)) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав: требуется роль admin",
        )
    return user

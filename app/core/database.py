"""Асинхронный движок SQLAlchemy и фабрика сессий."""
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
    connect_args={"timeout": 10},
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI-зависимость: выдаёт сессию на время обработки запроса."""
    async with async_session() as session:
        yield session


__all__ = ["engine", "async_session", "get_db"]

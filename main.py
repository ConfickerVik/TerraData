import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api import analytics, admin, auth, converter, fias, nspd, rosreestr, sudrf
from app.core.database import async_session
from app.core.deps import require_auth
from app.services import auth_service

logger = logging.getLogger("terradata.bootstrap")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Идемпотентный bootstrap администратора
    try:
        async with async_session() as session:
            await auth_service.ensure_admin_user(session)
    except Exception as exc:
        logger.warning("Не удалось выполнить bootstrap администратора: %s", exc)
    yield


app = FastAPI(
    title="TerraData API",
    description="API for Rosreestr and NSPD data extraction and XML to PDF conversion",
    version="1.1.0",
    lifespan=lifespan,
)

# Публичные маршруты
app.include_router(auth.router)
app.include_router(converter.router)  # POST /converter/xml-to-pdf доступен без ключа

# Защищённые маршруты (требуют JWT или активный API-ключ)
app.include_router(admin.router)
app.include_router(rosreestr.router, dependencies=[Depends(require_auth)])
app.include_router(nspd.router, dependencies=[Depends(require_auth)])
app.include_router(fias.router, dependencies=[Depends(require_auth)])
app.include_router(sudrf.router, dependencies=[Depends(require_auth)])
app.include_router(analytics.router, dependencies=[Depends(require_auth)])


@app.get("/")
async def root():
    return {
        "message": "Welcome to TerraData API",
        "docs": "/docs",
        "endpoints": {
            "rosreestr": "/rosreestr",
            "converter": "/converter",
            "nspd": "/nspd",
            "fias": "/fias",
            "sudrf": "/sudrf",
            "analytics": "/analytics",
            "auth": "/auth",
            "admin": "/admin",
        },
    }


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    # Применяем миграции БД перед стартом сервера
    base_dir = Path(__file__).resolve().parent
    cfg = Config(str(base_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(base_dir / "alembic"))
    command.upgrade(cfg, "head")

    uvicorn.run(app, host="0.0.0.0", port=8080)

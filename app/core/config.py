"""Конфигурация приложения через переменные окружения (.env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Приложение
    app_name: str = "TerraData API"
    debug: bool = False

    # База данных
    # Приоритет: DATABASE_URL (env или .env) > значение по умолчанию.
    # Значение по умолчанию совпадает с docker-compose.yml (сервис db).
    database_url: str = "postgresql+asyncpg://terradata:terradata@localhost:5432/terradata"

    # JWT
    secret_key: str = "insecure-dev-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 1440

    # Bootstrap администратора (создаётся при старте, если admin_password задан)
    admin_username: str = "admin"
    admin_password: str = ""
    admin_email: str = ""

    # Квоты запросов
    default_daily_quota: int = 1000

    # CORS
    # Разрешённые origin через запятую, например:
    # "http://localhost:5173,https://app.example.com"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

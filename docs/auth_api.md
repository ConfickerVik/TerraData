# API Аутентификации и авторизации

TerraData защищает все эндпоинты, кроме:

- `POST /converter/xml-to-pdf` — публичная конвертация XML в PDF;
- `POST /auth/register`, `POST /auth/login` — вход и регистрация;
- служебных `/`, `/docs`, `/redoc`, `/openapi.json`.

## Механизмы доступа

| Механизм | Где передаётся | Назначение |
|---|---|---|
| **JWT** | `Authorization: Bearer <token>` | Интерактивные клиенты и фронтенд |
| **API-ключ** | `X-API-Key: <key>` | Серверные интеграции |

Оба механизма резолвятся в одного пользователя. Если передан `X-API-Key`, он имеет приоритет.

## Регистрация и вход

### `POST /auth/register`

```json
{
  "username": "alice",
  "password": "secret123",
  "email": "alice@example.com"
}
```

Возвращает `201` с данными пользователя (роль `user`). Повторная регистрация с тем же именем — `409`.

### `POST /auth/login`

```json
{
  "username": "alice",
  "password": "secret123"
}
```

Возвращает:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 86400
}
```

## Текущий пользователь

### `GET /auth/me` — `X-API-Key` или `Authorization: Bearer`

Возвращает профиль текущего пользователя (`id`, `username`, `email`, `role`, `is_active`, `request_limit`, `created_at`).

## Управление API-ключами (требуется авторизация)

| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `POST` | `/auth/api-keys` | Создать ключ. Полный ключ возвращается **один раз** |
| `GET` | `/auth/api-keys` | Список своих ключей (маскированные) |
| `PATCH` | `/auth/api-keys/{id}` | Активировать/деактивировать (`{"is_active": false}`) |
| `DELETE` | `/auth/api-keys/{id}` | Отозвать ключ |

Пример создания ключа:

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "prod-integration"}'
```

## Роли и администрирование

Роли: `user` и `admin`.

Эндпоинты `/admin/*` доступны только роли `admin`:

| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `GET` | `/admin/users` | Список пользователей |
| `GET` | `/admin/users/{id}` | Данные пользователя |
| `PATCH` | `/admin/users/{id}` | Изменить роль/статус/лимит |
| `DELETE` | `/admin/users/{id}` | Удалить пользователя |
| `GET` | `/admin/api-keys?user_id=` | Все ключи (опц. фильтр по пользователю) |
| `DELETE` | `/admin/api-keys/{id}` | Отозвать любой ключ |

При старте приложения идемпотентно создаётся администратор из переменных окружения
`ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` (если пароль задан).

## Квоты запросов

Роль `user` ограничена суточным лимитом запросов (по умолчанию `1000`, настраивается через
`DEFAULT_DAILY_QUOTA` и персонально — полем `request_limit` пользователя). Роль `admin`
не лимитирована. При превышении возвращается `429`.

## Коды ошибок

| Код | Условие |
| :--- | :--- |
| `401` | Отсутствуют или недействительны учётные данные / ключ деактивирован |
| `403` | Доступ к `/admin/*` без роли `admin` |
| `409` | Пользователь с таким именем уже существует |
| `429` | Превышен суточный лимит запросов |

## Переменные окружения

| Переменная | Описание |
| :--- | :--- |
| `DATABASE_URL` | DSN PostgreSQL (asyncpg) |
| `SECRET_KEY` | Секрет для подписи JWT |
| `JWT_ALGORITHM` | Алгоритм JWT (по умолчанию `HS256`) |
| `JWT_EXPIRES_MINUTES` | Время жизни токена (мин) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | Bootstrap администратора |
| `DEFAULT_DAILY_QUOTA` | Суточный лимит для роли `user` |

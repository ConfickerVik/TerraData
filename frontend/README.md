# TerraData Frontend

Клиентское приложение TerraData на **Vite + React + TypeScript + Material UI**.

## Запуск

```bash
# из папки frontend/
npm install
npm run dev
```

Dev-сервер стартует на `http://localhost:5173`. Бэкенд должен быть доступен на
`http://localhost:8000` (Docker) или на порту из `VITE_API_BASE_URL`.

### Переменные окружения

Создайте `frontend/.env` (пример в `.env.example`):

```bash
# URL бэкенда (по умолчанию http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

Фронт ходит на бэкенд напрямую по **CORS** (прокси не используется). Разрешённые
origin задаются на бэкенде через `CORS_ORIGINS` в `.env`.

## Скрипты

- `npm run dev` — dev-сервер Vite.
- `npm run build` — typecheck + production-сборка в `dist/`.
- `npm run typecheck` — только проверка типов.
- `npm run generate:api` — перегенерировать `src/api/schema.d.ts` из OpenAPI
  (нужен запущенный бэкенд на `:8000`).

## Структура

```text
src/
├── api/            # HTTP-клиент, типы DTO, хранение токена
├── app/            # тема, роутер, layout'ы
├── features/       # фичи (auth, rosreestr, ...) — API + хуки
├── pages/          # страницы (по одной на модуль API)
├── shared/         # переиспользуемые компоненты
├── App.tsx         # корневой компонент
├── main.tsx        # точка входа + провайдеры
└── config.ts       # API_BASE_URL
```

## Авторизация

JWT хранится в `localStorage` и автоматически подставляется в заголовок
`Authorization` для всех запросов. При ответе `401` клиент поднимает событие,
которое разлогинивает пользователя и возвращает на `/login`.

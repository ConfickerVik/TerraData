// Базовый URL бэкенда. Переопределяется через переменную окружения
// VITE_API_BASE_URL в файле frontend/.env (например, для продакшн-домена).
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

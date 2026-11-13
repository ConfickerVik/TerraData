// Типы DTO, зеркалящие Pydantic-схемы бэкенда (app/schemas/*).
// При поднятом бэкенде их можно перегенерировать из OpenAPI:
//   npm run generate:api  →  src/api/schema.d.ts

export interface RegisterRequest {
  username: string
  password: string
  email?: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserOut {
  id: number
  username: string
  email: string | null
  role: string
  is_active: boolean
  request_limit: number | null
  created_at: string | null
}

export interface ApiKeyOut {
  id: number
  name: string
  key_prefix: string
  is_active: boolean
  created_at: string | null
  last_used_at: string | null
}

export interface ApiKeyCreated extends ApiKeyOut {
  key: string
}

export interface ApiKeyCreate {
  name: string
}

export interface ApiKeyToggle {
  is_active: boolean
}

// Росреестр возвращает сырой вложенный JSON — типизируем свободно,
// для UI важнее фактические ключи конкретного ответа.
export type RosreestrInfo = Record<string, unknown>

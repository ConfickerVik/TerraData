import { apiFetch } from '../../api/client'
import type {
  ApiKeyCreate,
  ApiKeyCreated,
  ApiKeyOut,
  ApiKeyToggle,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserOut,
} from '../../api/types'

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function register(payload: RegisterRequest): Promise<UserOut> {
  return apiFetch<UserOut>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getMe(): Promise<UserOut> {
  return apiFetch<UserOut>('/auth/me')
}

export function listApiKeys(): Promise<ApiKeyOut[]> {
  return apiFetch<ApiKeyOut[]>('/auth/api-keys')
}

export function createApiKey(payload: ApiKeyCreate): Promise<ApiKeyCreated> {
  return apiFetch<ApiKeyCreated>('/auth/api-keys', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function toggleApiKey(id: number, payload: ApiKeyToggle): Promise<ApiKeyOut> {
  return apiFetch<ApiKeyOut>(`/auth/api-keys/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteApiKey(id: number): Promise<void> {
  return apiFetch<void>(`/auth/api-keys/${id}`, { method: 'DELETE' })
}

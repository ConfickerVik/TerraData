import { API_BASE_URL } from '../config'
import { getAccessToken } from './token'

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

// Событие, которое поднимаем при 401 — AuthProvider слушает его и разлогинивает.
export const UNAUTHORIZED_EVENT = 'terradata:unauthorized'

function isFormData(body: unknown): body is FormData {
  return typeof FormData !== 'undefined' && body instanceof FormData
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const body = options.body

  // Для FormData браузер сам выставит Content-Type с boundary.
  if (body !== undefined && !isFormData(body)) {
    headers.set('Content-Type', 'application/json')
  }

  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers, body })

  if (response.status === 401) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
  }

  if (!response.ok) {
    let detail: unknown
    try {
      detail = await response.json()
    } catch {
      detail = undefined
    }
    throw new ApiError(response.status, `HTTP ${response.status}`, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

// Достаёт человекочитаемое сообщение об ошибке из FastAPI-ответа `{ detail: ... }`.
export function getApiErrorDetail(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = error.detail
    if (detail && typeof detail === 'object' && 'detail' in detail) {
      const message = (detail as { detail?: unknown }).detail
      if (typeof message === 'string') return message
    }
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Неизвестная ошибка'
}

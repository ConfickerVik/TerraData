import { apiFetch } from '../../api/client'
import type { ApiKeyAdminOut, UserAdminUpdate, UserOut } from '../../api/types'

export function listUsers(): Promise<UserOut[]> {
  return apiFetch<UserOut[]>('/admin/users')
}

export function updateUser(id: number, payload: UserAdminUpdate): Promise<UserOut> {
  return apiFetch<UserOut>(`/admin/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteUser(id: number): Promise<void> {
  return apiFetch<void>(`/admin/users/${id}`, { method: 'DELETE' })
}

export function listAllApiKeys(): Promise<ApiKeyAdminOut[]> {
  return apiFetch<ApiKeyAdminOut[]>('/admin/api-keys')
}

export function revokeAnyKey(id: number): Promise<void> {
  return apiFetch<void>(`/admin/api-keys/${id}`, { method: 'DELETE' })
}

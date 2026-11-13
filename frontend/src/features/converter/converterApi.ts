import { API_BASE_URL } from '../../config'
import { getAccessToken } from '../../api/token'
import { ApiError } from '../../api/client'

export interface ConvertResult {
  blob: Blob
  filename: string
}

// Отправляет XML на /converter/xml-to-pdf (multipart) и возвращает PDF как Blob.
// Эндпоинт публичный, но токен передаём, если он есть — не помешает.
export async function convertXmlToPdf(file: File): Promise<ConvertResult> {
  const formData = new FormData()
  formData.append('file', file)

  const headers = new Headers()
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE_URL}/converter/xml-to-pdf`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    let detail: unknown
    try {
      detail = await response.json()
    } catch {
      detail = undefined
    }
    throw new ApiError(response.status, `HTTP ${response.status}`, detail)
  }

  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const match = /filename="?([^";]+)"?/.exec(disposition)
  const filename = match ? match[1] : 'converted.pdf'

  return { blob, filename }
}

import { API_BASE_URL } from '../../config'
import { getAccessToken } from '../../api/token'
import { ApiError } from '../../api/client'

export interface ReportRequest {
  cad_num: string
  include_nspd: boolean
  include_fias: boolean
  include_sudrf: boolean
}

export interface GenerateReportResult {
  blob: Blob
  filename: string
}

// Генерирует аналитический PDF-отчёт: POST /analytics/generate-report (JSON)
// и возвращает PDF как Blob. Имя файла берётся из Content-Disposition.
export async function generateReport(payload: ReportRequest): Promise<GenerateReportResult> {
  const headers = new Headers()
  headers.set('Content-Type', 'application/json')
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE_URL}/analytics/generate-report`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
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
  const filename = match ? match[1] : `report_${payload.cad_num}.pdf`

  return { blob, filename }
}

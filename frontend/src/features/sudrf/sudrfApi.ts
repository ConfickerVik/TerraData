import { apiFetch } from '../../api/client'
import type {
  SudrfCourtInfoResponse,
  SudrfCourtsResponse,
  SudrfObjectIdResponse,
} from '../../api/types'

export function getCourtsByFias(fiasId: string): Promise<SudrfCourtsResponse> {
  return apiFetch<SudrfCourtsResponse>(`/sudrf/by-fias?fias_id=${encodeURIComponent(fiasId)}`)
}

export function getCourtByCadastral(cadNum: string): Promise<SudrfCourtInfoResponse> {
  return apiFetch<SudrfCourtInfoResponse>(
    `/sudrf/by-cadastral?cad_num=${encodeURIComponent(cadNum)}`,
  )
}

export function getCourtByAddress(address: string): Promise<SudrfCourtInfoResponse> {
  return apiFetch<SudrfCourtInfoResponse>(
    `/sudrf/by-address?address=${encodeURIComponent(address)}`,
  )
}

export function getCourtByObjectId(objectId: string): Promise<SudrfObjectIdResponse> {
  return apiFetch<SudrfObjectIdResponse>(
    `/sudrf/by-object-id?object_id=${encodeURIComponent(objectId)}`,
  )
}

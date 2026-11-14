import { apiFetch } from '../../api/client'
import type { FiasAddressHint, FiasByCadastralResponse } from '../../api/types'

export function getFiasByCadastral(cadNum: string): Promise<FiasByCadastralResponse> {
  return apiFetch<FiasByCadastralResponse>(
    `/fias/by-cadastral?cad_num=${encodeURIComponent(cadNum)}`,
  )
}

export function searchFiasAddress(address: string): Promise<FiasAddressHint[]> {
  return apiFetch<FiasAddressHint[]>(
    `/fias/search-address?address=${encodeURIComponent(address)}`,
  )
}

export function getFiasByObjectId(objectId: number | string): Promise<FiasByCadastralResponse> {
  return apiFetch<FiasByCadastralResponse>(
    `/fias/by-object-id?object_id=${encodeURIComponent(String(objectId))}`,
  )
}

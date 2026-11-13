import { apiFetch } from '../../api/client'
import type { AddressSearchItem, RosreestrInfoResponse } from '../../api/types'

export function getPropertyInfo(cadNum: string): Promise<RosreestrInfoResponse> {
  return apiFetch<RosreestrInfoResponse>(`/rosreestr/info?cad_num=${encodeURIComponent(cadNum)}`)
}

export function searchByAddress(address: string): Promise<AddressSearchItem[]> {
  return apiFetch<AddressSearchItem[]>(
    `/rosreestr/search-address?address=${encodeURIComponent(address)}`,
  )
}

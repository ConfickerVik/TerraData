import { apiFetch } from '../../api/client'
import type { RosreestrInfo } from '../../api/types'

export function getPropertyInfo(cadNum: string): Promise<RosreestrInfo> {
  return apiFetch<RosreestrInfo>(`/rosreestr/info?cad_num=${encodeURIComponent(cadNum)}`)
}

export function searchByAddress(address: string): Promise<RosreestrInfo> {
  return apiFetch<RosreestrInfo>(
    `/rosreestr/search-address?address=${encodeURIComponent(address)}`,
  )
}

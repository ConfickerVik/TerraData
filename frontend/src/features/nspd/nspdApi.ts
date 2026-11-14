import { apiFetch } from '../../api/client'
import type { NspdCadastralPriceResponse, NspdPropertyResponse } from '../../api/types'

export function getCadastralPrice(cadNum: string): Promise<NspdCadastralPriceResponse> {
  return apiFetch<NspdCadastralPriceResponse>(
    `/nspd/cadastral-price?cad_num=${encodeURIComponent(cadNum)}`,
  )
}

export function getProperty(cadNum: string): Promise<NspdPropertyResponse> {
  return apiFetch<NspdPropertyResponse>(
    `/nspd/property?cad_num=${encodeURIComponent(cadNum)}`,
  )
}

export interface NspdDetailParams {
  objdocId: number
  registersId?: number
  categoryId: number
}

function getDetail(path: string, params: NspdDetailParams): Promise<unknown> {
  const search = new URLSearchParams({
    objdocId: String(params.objdocId),
    categoryId: String(params.categoryId),
  })
  if (params.registersId !== undefined) {
    search.set('registersId', String(params.registersId))
  }
  return apiFetch<unknown>(`/nspd/details/${path}?${search.toString()}`)
}

export const getObjectsList = (params: NspdDetailParams) => getDetail('objects-list', params)
export const getLandLinks = (params: NspdDetailParams) => getDetail('land-links', params)
export const getBuildParts = (params: NspdDetailParams) => getDetail('build-parts', params)
export const getPermissionTypes = (params: NspdDetailParams) =>
  getDetail('permission-types', params)

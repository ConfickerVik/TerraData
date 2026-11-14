// Типы DTO, зеркалящие Pydantic-схемы бэкенда (app/schemas/*).
// При поднятом бэкенде их можно перегенерировать из OpenAPI:
//   npm run generate:api  →  src/api/schema.d.ts

export interface RegisterRequest {
  username: string
  password: string
  email?: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserOut {
  id: number
  username: string
  email: string | null
  role: string
  is_active: boolean
  request_limit: number | null
  created_at: string | null
}

export interface ApiKeyOut {
  id: number
  name: string
  key_prefix: string
  is_active: boolean
  created_at: string | null
  last_used_at: string | null
}

export interface ApiKeyCreated extends ApiKeyOut {
  key: string
}

export interface ApiKeyCreate {
  name: string
}

export interface ApiKeyToggle {
  is_active: boolean
}

// ==== Росреестр ====

export interface RosreestrAddress {
  region: string | null
  district: string | null
  city: string | null
  cityType: string | null
  urbanDistrict: string | null
  urbanDistrictType: string | null
  sovietVillage: string | null
  sovietVillageType: string | null
  locality: string | null
  localityType: string | null
  street: string | null
  streetType: string | null
  house: string | null
  houseType: string | null
  building: string | null
  buildingType: string | null
  structure: string | null
  structureType: string | null
  apartment: string | null
  apartmentType: string | null
  liter: string | null
  addition: string | null
  address: string | null
  readableAddress: string | null
  fiasGuid: string | null
}

export interface MainCharacteristic {
  code: string | null
  description: string | null
  value: number | null
  unitCode: string | null
  unitDescription: string | null
}

export interface RosreestrRight {
  rightType: string | null
  rightRegDate: number | null
  rightNumber: string | null
  part: string | null
  ownershipType: string | null
  rightTypeDesc: string | null
  sharedOwnershipType: boolean | null
}

export interface RosreestrEncumbrance {
  startDate: number | null
  encumbranceNumber: string | null
  encumbranceDate: number | null
  type: string | null
  typeDesc: string | null
  rightNum: string | null
}

export interface RosreestrOldNumber {
  numType: string | null
  numValue: string | null
}

export interface RosreestrElement {
  objectId: string | null
  databaseName: string | null
  regionKey: string | null
  cadNumber: string | null
  cadQuarter: string | null
  status: string | null
  objType: string | null
  area: string | null
  address: RosreestrAddress | null
  regDate: number | null
  cancelDate: number | null
  rights: RosreestrRight[] | null
  encumbrances: RosreestrEncumbrance[] | null
  oldNumbers: RosreestrOldNumber[] | null
  landCategory: string | null
  permittedUse: string | null
  permittedUseByDoc: string | null
  cadCost: string | null
  cadCostDate: number | null
  cadCostDeterminationDate: number | null
  cadCostRegistrationDate: number | null
  infoUpdateDate: number | null
  cadEngFIO: string | null
  cadEngCertNumber: string | null
  cadEngPhone: string | null
  floor: string | null
  undergroundFloor: string | null
  levelFloor: string | null
  ownershipType: string | null
  oksWallMaterial: string | null
  oksCommisioningYear: number | null
  oksYearBuild: number | null
  purpose: string | null
  childCadNumbers: unknown | null
  parentCadNumber: string | null
  mainCharacters: MainCharacteristic[] | null
}

export interface RosreestrInfoResponse {
  elements: RosreestrElement[]
  count: number
}

export type AddressItemType = 'PARCEL' | 'OKS' | 'FLAT'

export interface AddressSearchItem {
  cadnum: string
  full_name: string
  actual: boolean | number | string
  type: AddressItemType
}

// ==== НСПД ====

export interface NspdGeometry {
  type: string | null
  coordinates: unknown
  crs: Record<string, unknown> | null
}

export interface NspdFeatureProperties {
  category: number | null
  categoryName: string | null
  options: Record<string, unknown> | null
  descr: string | null
  externalKey: string | null
  interactionId: number | null
  label: string | null
  cadastralDistrictsCode: number | null
  subcategory: number | null
  systemInfo: Record<string, unknown> | null
}

export interface NspdFeature {
  id: number | null
  type: string | null
  geometry: NspdGeometry | null
  properties: NspdFeatureProperties | null
}

export interface NspdCadastralPriceResponse {
  data: {
    type: string | null
    features: NspdFeature[]
  } | null
  meta: { totalCount: number | null; categoryId: number | null }[] | null
}

export interface NspdPropertyResponse {
  base_info: NspdCadastralPriceResponse | null
  geometry: Record<string, unknown> | null
  details: Record<string, unknown> | null
  message?: string | null
}

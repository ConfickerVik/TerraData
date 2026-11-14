import { Fragment, useState } from 'react'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  Link,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import CloseIcon from '@mui/icons-material/Close'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import type {
  NspdCadastralPriceResponse,
  NspdFeature,
  NspdGeometry,
  NspdPropertyResponse,
} from '../api/types'
import {
  getBuildParts,
  getCadastralPrice,
  getLandLinks,
  getObjectsList,
  getPermissionTypes,
  getProperty,
} from '../features/nspd/nspdApi'
import type { NspdDetailParams } from '../features/nspd/nspdApi'

type FieldKind = 'money' | 'date' | 'area'

interface FieldGroup {
  label: string
  keys: string[]
  kind?: FieldKind
}

// Порядок и подписи полей. Ключи-синонимы берутся из разных категорий
// (Здания / Земельные участки / Помещения) — выводится первый присутствующий.
const FIELD_GROUPS: FieldGroup[] = [
  { label: 'Кадастровый номер', keys: ['cad_num', 'cad_number'] },
  { label: 'Тип объекта', keys: ['type', 'params_type', 'land_record_type', 'build_record_type_value'] },
  { label: 'Наименование', keys: ['name', 'building_name'] },
  { label: 'Назначение', keys: ['purpose'] },
  { label: 'Адрес', keys: ['readable_address'] },
  { label: 'Площадь', keys: ['area', 'specified_area', 'build_record_area', 'declared_area'], kind: 'area' },
  { label: 'Этаж', keys: ['floor'] },
  { label: 'Этажей', keys: ['floors'] },
  { label: 'Подземных этажей', keys: ['underground_floors'] },
  { label: 'Год постройки', keys: ['year_built'] },
  { label: 'Год ввода в эксплуатацию', keys: ['year_commisioning'] },
  { label: 'Материал стен', keys: ['materials'] },
  { label: 'Категория земель', keys: ['land_record_category_type'] },
  { label: 'Вид', keys: ['land_record_subtype'] },
  {
    label: 'Разрешённое использование',
    keys: ['permitted_use_established_by_document', 'permitted_use_name'],
  },
  { label: 'Статус', keys: ['status', 'common_data_status', 'previously_posted'] },
  { label: 'Кадастровая стоимость', keys: ['cost_value'], kind: 'money' },
  { label: 'Удельный показатель стоимости', keys: ['cost_index'], kind: 'money' },
  { label: 'Форма собственности', keys: ['ownership_type'] },
  { label: 'Права', keys: ['right_type'] },
  {
    label: 'Дата постановки на учёт',
    keys: ['registration_date', 'build_record_registration_date', 'land_record_reg_date'],
    kind: 'date',
  },
  { label: 'Дата снятия', keys: ['cancel_date'], kind: 'date' },
  { label: 'Дата определения стоимости', keys: ['cost_determination_date'], kind: 'date' },
  { label: 'Дата внесения стоимости', keys: ['cost_registration_date'], kind: 'date' },
  { label: 'Дата применения', keys: ['cost_application_date'], kind: 'date' },
  { label: 'Дата утверждения', keys: ['cost_approvement_date'], kind: 'date' },
  { label: 'Основание определения стоимости', keys: ['determination_couse'] },
  { label: 'Родительский кадастровый номер', keys: ['parent_cad_number'] },
  { label: 'Кадастровый квартал', keys: ['quarter_cad_number'] },
  { label: 'Объект культурного наследия', keys: ['cultural_heritage_object', 'cultural_heritage_val'] },
]

function formatValue(value: unknown, kind?: FieldKind): string {
  if (Array.isArray(value)) {
    return value.map((v) => String(v)).join(', ')
  }
  if (value === null || value === undefined || value === '') return ''

  if (kind === 'money') {
    const num = Number(value)
    return Number.isNaN(num)
      ? String(value)
      : `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(num)} ₽`
  }
  if (kind === 'date') {
    const d = typeof value === 'number' ? new Date(value) : new Date(String(value))
    return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleDateString('ru-RU')
  }
  if (kind === 'area') {
    const num = Number(value)
    return Number.isNaN(num) ? `${String(value)} кв.м` : `${num.toLocaleString('ru-RU')} кв.м`
  }
  return String(value)
}

function extractFields(feature: NspdFeature): { label: string; value: string }[] {
  const options = feature.properties?.options ?? {}
  const fields: { label: string; value: string }[] = []

  for (const group of FIELD_GROUPS) {
    for (const key of group.keys) {
      const value = options[key]
      if (value === null || value === undefined || value === '') continue
      const text = formatValue(value, group.kind)
      if (text) {
        fields.push({ label: group.label, value: text })
      }
      break
    }
  }

  return fields
}

function getCadNum(feature: NspdFeature): string {
  const options = feature.properties?.options ?? {}
  const fromOptions = options['cad_num'] ?? options['cad_number']
  if (fromOptions) return String(fromOptions)
  return (
    feature.properties?.label ??
    feature.properties?.descr ??
    feature.properties?.externalKey ??
    'Без номера'
  )
}

function getAddress(feature: NspdFeature): string | null {
  const value = feature.properties?.options?.['readable_address']
  return value ? String(value) : null
}

interface CoordPoint {
  x: number
  y: number
}

function extractGeometry(
  geometry: NspdGeometry | null,
): { type: string; points: CoordPoint[] } | null {
  if (!geometry || !geometry.type) return null
  const coords = geometry.coordinates

  if (geometry.type === 'Point' && Array.isArray(coords)) {
    if (typeof coords[0] === 'number' && typeof coords[1] === 'number') {
      return { type: 'Точка центра', points: [{ x: coords[0], y: coords[1] }] }
    }
  }

  if (geometry.type === 'Polygon' && Array.isArray(coords)) {
    const points: CoordPoint[] = []
    for (const ring of coords) {
      if (!Array.isArray(ring)) continue
      for (const pair of ring) {
        if (Array.isArray(pair) && typeof pair[0] === 'number' && typeof pair[1] === 'number') {
          points.push({ x: pair[0], y: pair[1] })
        }
      }
    }
    if (points.length > 0) return { type: 'Полигон', points }
  }

  return null
}

const EARTH_RADIUS = 6378137.0
const MAX_EXTENT = 20037508.342789244

// EPSG:3857 (Web Mercator) -> EPSG:4326 (WGS 84), формула как в CoordsConverter бэкенда.
function normalizeCoord(x: number, y: number): { lat: number; lon: number } {
  const lat = Math.atan(Math.sinh(y / EARTH_RADIUS)) * (180 / Math.PI)
  const lon = (x / MAX_EXTENT) * 180
  return { lat, lon }
}

function formatCoord(value: number, normalized: boolean): string {
  return normalized ? value.toFixed(6) : value.toFixed(2)
}

function CoordinateSection({ geometry }: { geometry: NspdGeometry | null }) {
  const [normalized, setNormalized] = useState(false)
  const info = extractGeometry(geometry)
  if (!info) return null

  return (
    <Box sx={{ mt: 1.5 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        Координаты
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
        Тип координат: {info.type}
      </Typography>

      <ToggleButtonGroup
        value={normalized ? 'normalized' : 'original'}
        exclusive
        size="small"
        sx={{ mt: 1 }}
        onChange={(_event, value) => {
          if (value !== null) setNormalized(value === 'normalized')
        }}
      >
        <ToggleButton value="original">Исходные</ToggleButton>
        <ToggleButton value="normalized">Нормализованные</ToggleButton>
      </ToggleButtonGroup>

      <Table size="small" sx={{ mt: 1, maxWidth: 480 }}>
        <TableHead>
          <TableRow>
            <TableCell>№</TableCell>
            <TableCell align="right">{normalized ? 'Широта' : 'X'}</TableCell>
            <TableCell align="right">{normalized ? 'Долгота' : 'Y'}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {info.points.map((point, pointIndex) => {
            const latLon = normalized ? normalizeCoord(point.x, point.y) : null
            const col1 = latLon ? latLon.lat : point.x
            const col2 = latLon ? latLon.lon : point.y
            return (
              <TableRow key={pointIndex}>
                <TableCell>{pointIndex + 1}</TableCell>
                <TableCell align="right">{formatCoord(col1, normalized)}</TableCell>
                <TableCell align="right">{formatCoord(col2, normalized)}</TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </Box>
  )
}

function getDetailParams(feature: NspdFeature): NspdDetailParams | null {
  const id = feature.id
  const category = feature.properties?.category
  if (id === null || id === undefined || category === null || category === undefined) return null

  const registersId = feature.properties?.options?.['registersId']
  return {
    objdocId: id,
    categoryId: category,
    registersId: typeof registersId === 'number' ? registersId : undefined,
  }
}

type DetailKind = 'objects-list' | 'cad-list' | 'cad-text' | 'value-list'

interface DetailSectionDef {
  key: string
  title: string
  kind: DetailKind
  load: (params: NspdDetailParams) => Promise<unknown>
}

const DETAIL_SECTIONS: DetailSectionDef[] = [
  { key: 'objects_list', title: 'Список объектов', kind: 'objects-list', load: getObjectsList },
  { key: 'land_links', title: 'Связанные земельные участки', kind: 'cad-list', load: getLandLinks },
  { key: 'build_parts', title: 'Части здания', kind: 'cad-text', load: getBuildParts },
  {
    key: 'permission_types',
    title: 'Виды разрешённого использования',
    kind: 'value-list',
    load: getPermissionTypes,
  },
]

function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

// Ответы вкладок имеют ключ `value` (возможно, обёрнутый в `data.value`).
function getValue(data: unknown): unknown {
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if ('value' in obj) return obj['value']
    if ('data' in obj && obj['data'] && typeof obj['data'] === 'object') {
      const inner = obj['data'] as Record<string, unknown>
      if ('value' in inner) return inner['value']
    }
  }
  return data
}

function renderValueList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return value !== null && value !== undefined && value !== '' ? [String(value)] : []
  }
  return value
    .map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') {
        const obj = item as Record<string, unknown>
        const v = obj['value'] ?? obj['name'] ?? obj['label'] ?? obj['description']
        if (typeof v === 'string' && v) return v
        return ''
      }
      return ''
    })
    .filter((s) => s !== '')
}

function extractCadNumbers(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  const numbers: string[] = []
  for (const item of value) {
    if (typeof item === 'string' && item) {
      numbers.push(item)
      continue
    }
    if (item && typeof item === 'object') {
      const obj = item as Record<string, unknown>
      for (const key of ['cad_num', 'cad_number', 'cadnum', 'label', 'descr', 'externalKey']) {
        const v = obj[key]
        if (typeof v === 'string' && v) {
          numbers.push(v)
          break
        }
      }
    }
  }
  return numbers
}

interface ObjectsListGroup {
  title: string
  cadNumbers: string[]
}

function parseObjectsList(data: unknown): ObjectsListGroup[] {
  const obj = data && typeof data === 'object' ? (data as Record<string, unknown>) : {}
  const entries = Array.isArray(obj['object']) ? (obj['object'] as unknown[]) : []

  const counts = new Map<string, string>()
  const lists = new Map<string, string[]>()

  for (const entry of entries) {
    if (!entry || typeof entry !== 'object') continue
    const e = entry as Record<string, unknown>
    const title = typeof e['title'] === 'string' ? e['title'] : ''
    const value = Array.isArray(e['value']) ? (e['value'] as string[]) : []

    if (title.endsWith('(количество)')) {
      const typeName = title.replace('(количество)', '').trim()
      counts.set(typeName, value[0] ?? '')
    } else if (title.endsWith('(список)')) {
      const typeName = title.replace('(список)', '').trim()
      lists.set(typeName, value.filter((v) => v !== ''))
    }
  }

  const groups: ObjectsListGroup[] = []
  const typeNames = Array.from(new Set([...counts.keys(), ...lists.keys()]))
  for (const typeName of typeNames) {
    const count = counts.get(typeName) ?? ''
    groups.push({
      title: count ? `${typeName} (${count})` : typeName,
      cadNumbers: lists.get(typeName) ?? [],
    })
  }
  return groups
}

function renderObjectsList(raw: unknown, onOpenCadNum?: (cadNum: string) => void) {
  const groups = parseObjectsList(raw)
  if (groups.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        Нет данных
      </Typography>
    )
  }

  return (
    <Stack spacing={1}>
      {groups.map((group, groupIndex) => (
        <Accordion key={groupIndex} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {group.title}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {group.cadNumbers.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Нет данных
              </Typography>
            ) : (
              <Stack spacing={0.5}>
                {group.cadNumbers.map((num, numIndex) => (
                  <Link
                    key={numIndex}
                    component="button"
                    variant="body2"
                    underline="hover"
                    sx={{ textAlign: 'left' }}
                    onClick={() => onOpenCadNum?.(num)}
                  >
                    {num}
                  </Link>
                ))}
              </Stack>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Stack>
  )
}

function DetailSection({
  title,
  kind,
  mode,
  load,
  params,
  data,
  onOpenCadNum,
}: {
  title: string
  kind: DetailKind
  mode: 'on-demand' | 'preloaded'
  load?: (params: NspdDetailParams) => Promise<unknown>
  params?: NspdDetailParams
  data?: unknown
  onOpenCadNum?: (cadNum: string) => void
}) {
  const [result, setResult] = useState<unknown>(undefined)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const value = mode === 'preloaded' ? data : result

  const handleLoad = async () => {
    if (!load || !params) return
    setLoading(true)
    setError(null)
    try {
      const res = await load(params)
      setResult(res)
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setResult(null)
      } else {
        setError(getApiErrorDetail(e))
      }
    } finally {
      setLoading(false)
    }
  }

  const showButton = mode === 'on-demand' && value === undefined && !error

  const renderBody = () => {
    if (isEmpty(value)) {
      return (
        <Typography variant="body2" color="text.secondary">
          Нет данных
        </Typography>
      )
    }

    const raw = getValue(value)

    if (kind === 'objects-list') {
      return renderObjectsList(raw, onOpenCadNum)
    }

    if (kind === 'value-list') {
      const list = renderValueList(raw)
      if (list.length === 0) {
        return (
          <Typography variant="body2" color="text.secondary">
            Нет данных
          </Typography>
        )
      }
      return (
        <Stack spacing={0.5}>
          {list.map((item, index) => (
            <Typography key={index} variant="body2">
              {item}
            </Typography>
          ))}
        </Stack>
      )
    }

    const nums = extractCadNumbers(raw)
    if (nums.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary">
          Нет данных
        </Typography>
      )
    }
    return (
      <Stack spacing={0.5}>
        {nums.map((num, index) =>
          kind === 'cad-list' ? (
            <Link
              key={index}
              component="button"
              variant="body2"
              underline="hover"
              sx={{ textAlign: 'left' }}
              onClick={() => onOpenCadNum?.(num)}
            >
              {num}
            </Link>
          ) : (
            <Typography key={index} variant="body2">
              {num}
            </Typography>
          )
        )}
      </Stack>
    )
  }

  return (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        {showButton && (
          <Button size="small" variant="outlined" onClick={handleLoad} disabled={loading}>
            {loading ? 'Загрузка…' : 'Загрузить'}
          </Button>
        )}
        {error && (
          <Typography variant="body2" color="error">
            {error}
          </Typography>
        )}
        {!showButton && !error && renderBody()}
      </AccordionDetails>
    </Accordion>
  )
}

function FeatureElement({
  feature,
  detailMode,
  details,
  showDetails = true,
  onOpenCadNum,
}: {
  feature: NspdFeature
  detailMode: 'on-demand' | 'preloaded'
  details?: Record<string, unknown> | null
  showDetails?: boolean
  onOpenCadNum?: (cadNum: string) => void
}) {
  const fields = extractFields(feature)
  const cadNum = getCadNum(feature)
  const address = getAddress(feature)
  const categoryName = feature.properties?.categoryName
  const detailParams = getDetailParams(feature)

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={1} flexWrap="wrap">
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          {cadNum}
        </Typography>
        {categoryName && <Chip label={categoryName} size="small" variant="outlined" />}
      </Stack>
      {address && (
        <Typography variant="body2" color="text.secondary">
          {address}
        </Typography>
      )}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '240px 1fr' },
          gap: 0.5,
          mt: 1,
        }}
      >
        {fields.map((field) => (
          <Fragment key={field.label}>
            <Typography variant="body2" color="text.secondary">
              {field.label}
            </Typography>
            <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
              {field.value}
            </Typography>
          </Fragment>
        ))}
      </Box>

      <CoordinateSection geometry={feature.geometry} />

      {showDetails && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Дополнительные сведения
          </Typography>
          <Stack spacing={1} sx={{ mt: 1 }}>
            {DETAIL_SECTIONS.map((section) => (
              <DetailSection
                key={section.key}
                title={section.title}
                kind={section.kind}
                mode={detailMode}
                load={section.load}
                params={detailParams ?? undefined}
                data={details ? details[section.key] : undefined}
                onOpenCadNum={onOpenCadNum}
              />
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  )
}

function NspdResult({
  data,
  onOpenCadNum,
}: {
  data: NspdCadastralPriceResponse
  onOpenCadNum: (cadNum: string) => void
}) {
  const features = data.data?.features ?? []

  if (features.length === 0) {
    return <Alert severity="info">По кадастровому номеру ничего не найдено.</Alert>
  }

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        Найдено элементов: {features.length}
      </Typography>
      <Stack spacing={2} divider={<Divider flexItem />}>
        {features.map((feature, index) => (
          <FeatureElement
            key={feature.id ?? index}
            feature={feature}
            detailMode="on-demand"
            onOpenCadNum={onOpenCadNum}
          />
        ))}
      </Stack>
    </Stack>
  )
}

function PropertyResult({
  data,
  onOpenCadNum,
}: {
  data: NspdPropertyResponse
  onOpenCadNum: (cadNum: string) => void
}) {
  const features = data.base_info?.data?.features ?? []
  const details = data.details ?? null

  if (features.length === 0) {
    return <Alert severity="info">По кадастровому номеру ничего не найдено.</Alert>
  }

  return (
    <Stack spacing={2}>
      {data.message && <Alert severity="info">{data.message}</Alert>}
      <Typography variant="body2" color="text.secondary">
        Найдено элементов: {features.length}
      </Typography>
      <Stack spacing={2} divider={<Divider flexItem />}>
        {features.map((feature, index) => (
          <FeatureElement
            key={feature.id ?? index}
            feature={feature}
            detailMode="preloaded"
            details={index === 0 ? details : null}
            onOpenCadNum={onOpenCadNum}
          />
        ))}
      </Stack>
    </Stack>
  )
}

export function NspdPage() {
  const [cadNum, setCadNum] = useState('')
  const [useProperty, setUseProperty] = useState(false)
  const [modalCadNum, setModalCadNum] = useState<string | null>(null)

  const cadastralMutation = useMutation<NspdCadastralPriceResponse, ApiError, string>({
    mutationFn: (num) => getCadastralPrice(num),
  })

  const propertyMutation = useMutation<NspdPropertyResponse, ApiError, string>({
    mutationFn: (num) => getProperty(num),
  })

  const infoQuery = useQuery<NspdCadastralPriceResponse, ApiError>({
    queryKey: ['nspd', 'cadastral-price', modalCadNum],
    queryFn: () => getCadastralPrice(modalCadNum as string),
    enabled: !!modalCadNum,
  })

  const handleSearch = () => {
    const trimmed = cadNum.trim()
    if (!trimmed) return
    if (useProperty) propertyMutation.mutate(trimmed)
    else cadastralMutation.mutate(trimmed)
  }

  const isPending = useProperty ? propertyMutation.isPending : cadastralMutation.isPending

  return (
    <Stack spacing={3}>
      <Typography variant="h4">НСПД</Typography>
      <Typography variant="body2" color="text.secondary">
        Кадастровая стоимость и базовые сведения об объекте из НСПД.
      </Typography>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField
          label="Кадастровый номер"
          placeholder="38:36:000029:1028"
          value={cadNum}
          onChange={(event) => setCadNum(event.target.value)}
          fullWidth
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={isPending || !cadNum.trim()}
          sx={{ minWidth: 160 }}
        >
          {isPending ? <CircularProgress size={24} color="inherit" /> : 'Найти'}
        </Button>
      </Stack>

      <FormControlLabel
        control={
          <Switch
            checked={useProperty}
            onChange={(_event, checked) => {
              setUseProperty(checked)
              cadastralMutation.reset()
              propertyMutation.reset()
            }}
          />
        }
        label="Полные сведения (endpoint /nspd/property)"
      />

      {useProperty ? (
        <>
          {propertyMutation.isError && (
            <Alert severity="error">{getApiErrorDetail(propertyMutation.error)}</Alert>
          )}
          {propertyMutation.isSuccess && propertyMutation.data && (
            <PropertyResult data={propertyMutation.data} onOpenCadNum={setModalCadNum} />
          )}
        </>
      ) : (
        <>
          {cadastralMutation.isError && (
            <Alert severity="error">{getApiErrorDetail(cadastralMutation.error)}</Alert>
          )}
          {cadastralMutation.isSuccess && cadastralMutation.data && (
            <NspdResult data={cadastralMutation.data} onOpenCadNum={setModalCadNum} />
          )}
        </>
      )}

      <Dialog
        open={!!modalCadNum}
        onClose={() => setModalCadNum(null)}
        maxWidth="md"
        fullWidth
        slotProps={{ backdrop: { sx: { backgroundColor: 'rgba(0, 0, 0, 0.32)' } } }}
      >
        <DialogTitle
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <Typography variant="h6" component="span">
            Сведения об объекте
          </Typography>
          <IconButton onClick={() => setModalCadNum(null)} size="small" aria-label="Закрыть">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {infoQuery.isPending && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          )}
          {infoQuery.isError && <Alert severity="error">{getApiErrorDetail(infoQuery.error)}</Alert>}
          {infoQuery.isSuccess && infoQuery.data?.data?.features?.length && (
            <FeatureElement
              feature={infoQuery.data.data.features[0]}
              detailMode="on-demand"
              showDetails={false}
            />
          )}
        </DialogContent>
      </Dialog>
    </Stack>
  )
}

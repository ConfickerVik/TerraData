import { useState } from 'react'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemText,
  Stack,
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
  AddressSearchItem,
  RosreestrElement,
  RosreestrInfoResponse,
} from '../api/types'
import { getPropertyInfo, searchByAddress } from '../features/rosreestr/rosreestrApi'

type SearchType = 'cadastral' | 'address'

function formatDate(value: number | null | undefined): string | null {
  if (value === null || value === undefined) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toLocaleDateString('ru-RU')
}

function formatMoney(value: string | null | undefined): string | null {
  if (value === null || value === undefined || value === '') return null
  const num = Number(value)
  if (Number.isNaN(num)) return value
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(num)} ₽`
}

function isOnRegistry(actual: boolean | number | string): boolean {
  return actual === true || actual === 1 || actual === '1'
}

interface InfoRow {
  label: string
  value: string
}

function buildCadastralRows(el: RosreestrElement): InfoRow[] {
  const rows: InfoRow[] = []
  const push = (label: string, value: string | number | null | undefined) => {
    if (value !== null && value !== undefined && value !== '') {
      rows.push({ label, value: String(value) })
    }
  }

  push('Кадастровый номер', el.cadNumber)
  push('Тип объекта', el.objType)
  push('Статус', el.status === '1' ? 'Актуальный' : el.status)
  push('Адрес', el.address?.readableAddress)

  if (el.area) {
    const area = Number(el.area)
    push('Площадь', `${Number.isNaN(area) ? el.area : area.toLocaleString('ru-RU')} кв.м`)
  }

  push('Кадастровая стоимость', formatMoney(el.cadCost))
  push('Дата определения кадастровой стоимости', formatDate(el.cadCostDeterminationDate))
  push('Дата внесения кадастровой стоимости', formatDate(el.cadCostRegistrationDate))
  push('Дата кадастровой стоимости', formatDate(el.cadCostDate))
  push('Дата постановки на учёт', formatDate(el.regDate))
  push('Дата снятия с учёта', formatDate(el.cancelDate))
  push('Дата обновления сведений', formatDate(el.infoUpdateDate))
  push('Этаж', el.floor)
  push('Подземных этажей', el.undergroundFloor)
  push('Материал стен', el.oksWallMaterial)
  push('Год ввода в эксплуатацию', el.oksCommisioningYear)
  push('Год постройки', el.oksYearBuild)
  push('Категория земель', el.landCategory)
  push('Разрешённое использование', el.permittedUse ?? el.permittedUseByDoc)
  push('Назначение', el.purpose)
  push('Форма собственности', el.ownershipType)
  push('Родительский кадастровый номер', el.parentCadNumber)

  for (const c of el.mainCharacters ?? []) {
    if (c.description && c.description !== 'Площадь' && c.value !== null && c.value !== undefined) {
      push(c.description, `${c.value}${c.unitDescription ? ` ${c.unitDescription}` : ''}`)
    }
  }

  return rows
}

function CadastralResult({ data }: { data: RosreestrInfoResponse }) {
  if (!data.elements || data.elements.length === 0) {
    return <Alert severity="info">По кадастровому номеру ничего не найдено.</Alert>
  }

  return (
    <Stack spacing={2}>
      {data.elements.map((el, index) => {
        const rows = buildCadastralRows(el)
        return (
          <Card key={el.cadNumber ?? index} variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {el.cadNumber ?? 'Объект недвижимости'}
              </Typography>
              <Stack spacing={0.5}>
                {rows.map((row) => (
                  <Box
                    key={row.label}
                    sx={{
                      display: 'flex',
                      flexDirection: { xs: 'column', sm: 'row' },
                      gap: { xs: 0, sm: 1 },
                    }}
                  >
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ width: { sm: 240 }, flexShrink: 0 }}
                    >
                      {row.label}
                    </Typography>
                    <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                      {row.value}
                    </Typography>
                  </Box>
                ))}
              </Stack>

              {el.rights && el.rights.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    Права
                  </Typography>
                  <Stack spacing={1} sx={{ mt: 1 }}>
                    {el.rights.map((right, rightIndex) => {
                      const regDate = formatDate(right.rightRegDate)
                      return (
                        <Box
                          key={rightIndex}
                          sx={{ pl: 1.5, borderLeft: '2px solid', borderColor: 'divider' }}
                        >
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {right.rightTypeDesc ?? 'Право'}
                          </Typography>
                          {right.rightNumber && (
                            <Typography variant="body2">Номер: {right.rightNumber}</Typography>
                          )}
                          {regDate && (
                            <Typography variant="body2">Дата регистрации: {regDate}</Typography>
                          )}
                        </Box>
                      )
                    })}
                  </Stack>
                </Box>
              )}

              {el.encumbrances && el.encumbrances.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    Обременения
                  </Typography>
                  <Stack spacing={1} sx={{ mt: 1 }}>
                    {el.encumbrances.map((enc, encIndex) => {
                      const startDate = formatDate(enc.startDate)
                      const encDate = formatDate(enc.encumbranceDate)
                      return (
                        <Box
                          key={encIndex}
                          sx={{ pl: 1.5, borderLeft: '2px solid', borderColor: 'divider' }}
                        >
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {enc.typeDesc ?? 'Обременение'}
                          </Typography>
                          {enc.encumbranceNumber && (
                            <Typography variant="body2">Номер: {enc.encumbranceNumber}</Typography>
                          )}
                          {startDate && (
                            <Typography variant="body2">Дата начала: {startDate}</Typography>
                          )}
                          {encDate && (
                            <Typography variant="body2">Дата обременения: {encDate}</Typography>
                          )}
                        </Box>
                      )
                    })}
                  </Stack>
                </Box>
              )}

              {el.oldNumbers && el.oldNumbers.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    Старые номера
                  </Typography>
                  <Stack spacing={0.5} sx={{ mt: 1 }}>
                    {el.oldNumbers.map((old, oldIndex) => (
                      <Typography key={oldIndex} variant="body2">
                        {old.numType}: {old.numValue}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              )}
            </CardContent>
          </Card>
        )
      })}
    </Stack>
  )
}

const TYPE_GROUPS = [
  { type: 'PARCEL', title: 'Земельные участки' },
  { type: 'OKS', title: 'Здания' },
  { type: 'FLAT', title: 'Квартиры / помещения' },
] as const

function AddressResult({
  data,
  onSelect,
}: {
  data: AddressSearchItem[]
  onSelect: (item: AddressSearchItem) => void
}) {
  if (data.length === 0) {
    return <Alert severity="info">По адресу ничего не найдено.</Alert>
  }

  return (
    <Stack spacing={1}>
      {TYPE_GROUPS.map((group) => {
        const items = data.filter((item) => item.type === group.type)
        return (
          <Accordion
            key={group.type}
            defaultExpanded={items.length > 0 && group.type !== 'FLAT'}
            disabled={items.length === 0}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {group.title}
                </Typography>
                <Chip label={items.length} size="small" color="primary" variant="outlined" />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {items.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Не найдено
                </Typography>
              ) : (
                <List dense>
                  {items.map((item) => {
                    const onRegistry = isOnRegistry(item.actual)
                    return (
                      <ListItem key={item.cadnum} divider>
                        <ListItemText
                          primary={
                            <Link
                              component="button"
                              variant="body2"
                              underline="hover"
                              onClick={() => onSelect(item)}
                              sx={{ fontWeight: 600 }}
                            >
                              {item.cadnum}
                            </Link>
                          }
                          secondary={item.full_name}
                        />
                        <Chip
                          label={onRegistry ? 'На учёте' : 'Не на учёте'}
                          color={onRegistry ? 'success' : 'default'}
                          size="small"
                          variant="outlined"
                        />
                      </ListItem>
                    )
                  })}
                </List>
              )}
            </AccordionDetails>
          </Accordion>
        )
      })}
    </Stack>
  )
}

export function RosreestrPage() {
  const [searchType, setSearchType] = useState<SearchType>('cadastral')
  const [query, setQuery] = useState('')
  const [selectedCadNum, setSelectedCadNum] = useState<string | null>(null)

  const cadastralMutation = useMutation<RosreestrInfoResponse, ApiError, string>({
    mutationFn: (num) => getPropertyInfo(num),
  })

  const addressMutation = useMutation<AddressSearchItem[], ApiError, string>({
    mutationFn: (addr) => searchByAddress(addr),
  })

  const infoQuery = useQuery<RosreestrInfoResponse, ApiError>({
    queryKey: ['rosreestr', 'info', selectedCadNum],
    queryFn: () => getPropertyInfo(selectedCadNum as string),
    enabled: !!selectedCadNum,
  })

  const isCadastral = searchType === 'cadastral'
  const isPending = isCadastral ? cadastralMutation.isPending : addressMutation.isPending

  const handleSearch = () => {
    const trimmed = query.trim()
    if (!trimmed) return
    if (isCadastral) {
      cadastralMutation.mutate(trimmed)
    } else {
      addressMutation.mutate(trimmed)
    }
  }

  const handleTypeChange = (_event: unknown, value: SearchType | null) => {
    if (value !== null && value !== searchType) {
      setSearchType(value)
      cadastralMutation.reset()
      addressMutation.reset()
    }
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Росреестр</Typography>
      <Typography variant="body2" color="text.secondary">
        Поиск сведений об объекте недвижимости по кадастровому номеру или адресу.
      </Typography>

      <ToggleButtonGroup value={searchType} exclusive size="small" onChange={handleTypeChange}>
        <ToggleButton value="cadastral">Кадастровый номер</ToggleButton>
        <ToggleButton value="address">Адрес</ToggleButton>
      </ToggleButtonGroup>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField
          label={isCadastral ? 'Кадастровый номер' : 'Адрес'}
          placeholder={isCadastral ? '38:00:000000:00001' : 'г. Иркутск, ул. Ленина, д. 1'}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          fullWidth
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={isPending || !query.trim()}
          sx={{ minWidth: 160 }}
        >
          {isPending ? <CircularProgress size={24} color="inherit" /> : 'Найти'}
        </Button>
      </Stack>

      {isCadastral ? (
        <>
          {cadastralMutation.isError && (
            <Alert severity="error">{getApiErrorDetail(cadastralMutation.error)}</Alert>
          )}
          {cadastralMutation.isSuccess && cadastralMutation.data && (
            <CadastralResult data={cadastralMutation.data} />
          )}
        </>
      ) : (
        <>
          {addressMutation.isError && (
            <Alert severity="error">{getApiErrorDetail(addressMutation.error)}</Alert>
          )}
          {addressMutation.isSuccess && addressMutation.data && (
            <AddressResult
              data={addressMutation.data}
              onSelect={(item) => setSelectedCadNum(item.cadnum)}
            />
          )}
        </>
      )}

      <Dialog
        open={!!selectedCadNum}
        onClose={() => setSelectedCadNum(null)}
        maxWidth="md"
        fullWidth
        slotProps={{
          backdrop: { sx: { backgroundColor: 'rgba(0, 0, 0, 0.32)' } },
        }}
      >
        <DialogTitle
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <Typography variant="h6" component="span">
            Сведения об объекте
          </Typography>
          <IconButton onClick={() => setSelectedCadNum(null)} size="small" aria-label="Закрыть">
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
          {infoQuery.isSuccess && infoQuery.data && <CadastralResult data={infoQuery.data} />}
        </DialogContent>
      </Dialog>
    </Stack>
  )
}

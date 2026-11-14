import { Fragment, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Link,
  Stack,
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
import { useMutation, useQuery } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import type {
  FiasAddress,
  FiasAddressHint,
  FiasByCadastralResponse,
  FiasHierarchyItem,
  FiasObjectDetails,
} from '../api/types'
import { getFiasByCadastral, getFiasByObjectId, searchFiasAddress } from '../features/fias/fiasApi'

type SearchType = 'cadastral' | 'address'

interface InfoRow {
  label: string
  value: string
}

function FieldGrid({ rows }: { rows: InfoRow[] }) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: '280px 1fr' },
        gap: 0.5,
      }}
    >
      {rows.map((row) => (
        <Fragment key={row.label}>
          <Typography variant="body2" color="text.secondary">
            {row.label}
          </Typography>
          <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
            {row.value}
          </Typography>
        </Fragment>
      ))}
    </Box>
  )
}

function buildAddressRows(addr: FiasAddress): InfoRow[] {
  const rows: InfoRow[] = []
  const push = (label: string, value: string | number | null | undefined) => {
    if (value !== null && value !== undefined && value !== '') {
      rows.push({ label, value: String(value) })
    }
  }
  const d = addr.address_details
  push('Кадастровый номер', d?.cadastral_number)
  push('Почтовый индекс', d?.postal_code)
  push('ОКАТО', d?.okato)
  push('ОКТМО', d?.oktmo)
  push('ОКТМО (бюджет)', d?.oktmo_budget)
  push('ИФНС (юр. лица)', d?.ifns_ul)
  push('ИФНС (физ. лица)', d?.ifns_fl)
  push('ИФНС террит. (юр. лица)', d?.ifns_tul)
  push('ИФНС террит. (физ. лица)', d?.ifns_tfl)
  push('Многоквартирный дом', d?.apart_building === '1' ? 'Да' : d?.apart_building)
  push('Код региона', addr.region_code)
  if (addr.is_active !== null && addr.is_active !== undefined) {
    push('Активен', addr.is_active ? 'Да' : 'Нет')
  }
  return rows
}

function buildObjectDetailsRows(d: FiasObjectDetails): InfoRow[] {
  const rows: InfoRow[] = []
  const push = (label: string, value: string | null | undefined) => {
    if (value !== null && value !== undefined && value !== '') {
      rows.push({ label, value })
    }
  }
  push('Реестровый номер', d.ReesterNumber)
  push('Дата начала действия', d.StartDate)
  push('Дата обновления', d.UpdateDate)
  push('Нормативный документ', d.NormativeDocument)
  push('Федеральный округ', d.FederalDistrict)
  if (d.AdminCenterRF !== null && d.AdminCenterRF !== undefined) {
    push('Административный центр РФ', d.AdminCenterRF ? 'Да' : 'Нет')
  }
  if (d.AdminCenterMunDistrict !== null && d.AdminCenterMunDistrict !== undefined) {
    push('Админ. центр муниц. района', d.AdminCenterMunDistrict ? 'Да' : 'Нет')
  }
  return rows
}

function HierarchyTable({ hierarchy }: { hierarchy: FiasHierarchyItem[] }) {
  if (!hierarchy || hierarchy.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        Нет данных
      </Typography>
    )
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Уровень</TableCell>
          <TableCell>Тип</TableCell>
          <TableCell>Название</TableCell>
          <TableCell>Полное наименование</TableCell>
          <TableCell>КЛАДР</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {hierarchy.map((item, index) => (
          <TableRow key={index}>
            <TableCell>{item.hierarchy_place ?? ''}</TableCell>
            <TableCell>{item.type_name ?? item.object_type ?? ''}</TableCell>
            <TableCell>{item.name ?? item.number ?? ''}</TableCell>
            <TableCell>{item.full_name ?? ''}</TableCell>
            <TableCell>{item.kladr_code ?? ''}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function FiasInfoView({ data }: { data: FiasByCadastralResponse }) {
  const addresses = data.addresses ?? []
  if (addresses.length === 0) {
    return <Alert severity="info">Сведения не найдены.</Alert>
  }

  return (
    <Stack spacing={3}>
      {addresses.map((addr, index) => (
        <Box key={addr.object_id ?? index}>
          <Typography variant="h6" gutterBottom>
            {addr.full_name ?? 'Адрес'}
          </Typography>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 2 }}>
            Основные сведения
          </Typography>
          <Box sx={{ mt: 0.5 }}>
            <FieldGrid rows={buildAddressRows(addr)} />
          </Box>

          {addr.federal_district?.full_name && (
            <Box sx={{ mt: 2 }}>
              <FieldGrid
                rows={[{ label: 'Федеральный округ', value: addr.federal_district.full_name }]}
              />
            </Box>
          )}

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 2 }}>
            Иерархия адреса
          </Typography>
          <Box sx={{ mt: 0.5 }}>
            <HierarchyTable hierarchy={addr.hierarchy ?? []} />
          </Box>
        </Box>
      ))}

      {data.object_details && (
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Сведения объекта
          </Typography>
          <Box sx={{ mt: 0.5 }}>
            <FieldGrid rows={buildObjectDetailsRows(data.object_details)} />
          </Box>
        </Box>
      )}
    </Stack>
  )
}

export function FiasPage() {
  const [searchType, setSearchType] = useState<SearchType>('cadastral')
  const [query, setQuery] = useState('')
  const [selectedObjectId, setSelectedObjectId] = useState<number | string | null>(null)

  const cadastralMutation = useMutation<FiasByCadastralResponse, ApiError, string>({
    mutationFn: (num) => getFiasByCadastral(num),
  })

  const addressMutation = useMutation<FiasAddressHint[], ApiError, string>({
    mutationFn: (addr) => searchFiasAddress(addr),
  })

  const objectIdQuery = useQuery<FiasByCadastralResponse, ApiError>({
    queryKey: ['fias', 'object-id', selectedObjectId],
    queryFn: () => getFiasByObjectId(selectedObjectId as number | string),
    enabled: selectedObjectId !== null,
  })

  const isCadastral = searchType === 'cadastral'
  const isPending = isCadastral ? cadastralMutation.isPending : addressMutation.isPending

  const handleSearch = () => {
    const trimmed = query.trim()
    if (!trimmed) return
    if (isCadastral) {
      cadastralMutation.mutate(trimmed)
    } else {
      setSelectedObjectId(null)
      addressMutation.mutate(trimmed)
    }
  }

  const handleTypeChange = (_event: unknown, value: SearchType | null) => {
    if (value !== null && value !== searchType) {
      setSearchType(value)
      cadastralMutation.reset()
      addressMutation.reset()
      setSelectedObjectId(null)
    }
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">ФИАС</Typography>
      <Typography variant="body2" color="text.secondary">
        Поиск адресов и сведений об объектах в ФИАС.
      </Typography>

      <ToggleButtonGroup value={searchType} exclusive size="small" onChange={handleTypeChange}>
        <ToggleButton value="cadastral">Кадастровый номер</ToggleButton>
        <ToggleButton value="address">Адрес</ToggleButton>
      </ToggleButtonGroup>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField
          label={isCadastral ? 'Кадастровый номер' : 'Адрес'}
          placeholder={isCadastral ? '38:36:000029:1028' : 'г. Иркутск, ул. Помяловского, д. 22'}
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
            <FiasInfoView data={cadastralMutation.data} />
          )}
        </>
      ) : (
        <>
          {addressMutation.isError && (
            <Alert severity="error">{getApiErrorDetail(addressMutation.error)}</Alert>
          )}
          {addressMutation.isSuccess && addressMutation.data && (
            <Stack spacing={2}>
              <Typography variant="body2" color="text.secondary">
                Найдено вариантов: {addressMutation.data.length}
              </Typography>
              <Stack spacing={0.5}>
                {addressMutation.data.map((hint) => (
                  <Link
                    key={hint.object_id}
                    component="button"
                    variant="body2"
                    underline="hover"
                    sx={{ textAlign: 'left' }}
                    onClick={() => setSelectedObjectId(hint.object_id)}
                  >
                    {hint.value}
                  </Link>
                ))}
              </Stack>

              {objectIdQuery.isPending && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              )}
              {objectIdQuery.isError && (
                <Alert severity="error">{getApiErrorDetail(objectIdQuery.error)}</Alert>
              )}
              {objectIdQuery.isSuccess && objectIdQuery.data && (
                <FiasInfoView data={objectIdQuery.data} />
              )}
            </Stack>
          )}
        </>
      )}
    </Stack>
  )
}

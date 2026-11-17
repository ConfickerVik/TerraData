import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Link,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import type { SudrfCourt } from '../api/types'
import {
  getCourtByAddress,
  getCourtByCadastral,
  getCourtByObjectId,
  getCourtsByFias,
} from '../features/sudrf/sudrfApi'

const COURT_TYPES: Record<string, string> = {
  MS: 'Судебный участок',
  RS: 'Районный суд',
  OS: 'Областной суд',
  AJ: 'Апелляционный суд',
  KJ: 'Кассационный суд',
  GV: 'Гарнизонный военный суд',
  OV: 'Окружной военный суд',
  AV: 'Апелляционный военный суд',
  KV: 'Кассационный военный суд',
  VS: 'Верховный суд',
}

function courtTypeLabel(code: string): string {
  return COURT_TYPES[code] ?? code ?? 'Суд'
}

type Method = 'fias' | 'cadastral' | 'address' | 'object-id'

const METHOD_OPTIONS: {
  value: Method
  label: string
  fieldLabel: string
  placeholder: string
}[] = [
  {
    value: 'fias',
    label: 'FIAS ID',
    fieldLabel: 'FIAS ID (GUID)',
    placeholder: '6466c988-7ce3-45e5-8b97-90ae16cb1249',
  },
  {
    value: 'cadastral',
    label: 'Кадастр',
    fieldLabel: 'Кадастровый номер',
    placeholder: '38:36:000029:1028',
  },
  {
    value: 'address',
    label: 'Адрес',
    fieldLabel: 'Адрес',
    placeholder: 'г. Иркутск, ул. Помяловского, д. 22',
  },
  {
    value: 'object-id',
    label: 'Object ID',
    fieldLabel: 'Object ID',
    placeholder: '67352892',
  },
]

function CourtItem({ court }: { court: SudrfCourt }) {
  return (
    <Box>
      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
        {court.name}
      </Typography>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '180px 1fr' },
          gap: 0.5,
          mt: 0.5,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Тип суда
        </Typography>
        <Typography variant="body2">{courtTypeLabel(court.type)}</Typography>

        <Typography variant="body2" color="text.secondary">
          Код (ВНКОД)
        </Typography>
        <Typography variant="body2">{court.vncod}</Typography>

        <Typography variant="body2" color="text.secondary">
          Адрес
        </Typography>
        <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
          {court.address}
        </Typography>

        <Typography variant="body2" color="text.secondary">
          Сайт
        </Typography>
        <Link
          href={court.url}
          target="_blank"
          rel="noopener noreferrer"
          variant="body2"
          sx={{ wordBreak: 'break-all' }}
        >
          {court.url}
        </Link>
      </Box>
    </Box>
  )
}

function CourtList({ courts }: { courts: SudrfCourt[] }) {
  if (courts.length === 0) {
    return <Alert severity="info">Суды не найдены.</Alert>
  }

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        Найдено судов: {courts.length}
      </Typography>
      <Stack spacing={2} divider={<Divider flexItem />}>
        {courts.map((court, index) => (
          <CourtItem key={court.vncod ?? index} court={court} />
        ))}
      </Stack>
    </Stack>
  )
}

export function SudrfPage() {
  const [method, setMethod] = useState<Method>('cadastral')
  const [query, setQuery] = useState('')

  const mutation = useMutation<SudrfCourt[], ApiError, void>({
    mutationFn: async () => {
      const q = query.trim()
      switch (method) {
        case 'fias': {
          const res = await getCourtsByFias(q)
          return res.courts ?? []
        }
        case 'cadastral': {
          const res = await getCourtByCadastral(q)
          return res.court_info?.courts ?? []
        }
        case 'address': {
          const res = await getCourtByAddress(q)
          return res.court_info?.courts ?? []
        }
        case 'object-id': {
          const res = await getCourtByObjectId(q)
          return res.court_info?.courts ?? []
        }
      }
    },
  })

  const current = METHOD_OPTIONS.find((option) => option.value === method) ?? METHOD_OPTIONS[0]

  return (
    <Stack spacing={3}>
      <Typography variant="h4">СУДРФ</Typography>
      <Typography variant="body2" color="text.secondary">
        Определение судебного участка и иерархии судов.
      </Typography>

      <ToggleButtonGroup
        value={method}
        exclusive
        size="small"
        onChange={(_event, value: Method | null) => {
          if (value !== null && value !== method) {
            setMethod(value)
            mutation.reset()
          }
        }}
      >
        {METHOD_OPTIONS.map((option) => (
          <ToggleButton key={option.value} value={option.value}>
            {option.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField
          label={current.fieldLabel}
          placeholder={current.placeholder}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          fullWidth
        />
        <Button
          variant="contained"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !query.trim()}
          sx={{ minWidth: 160 }}
        >
          {mutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Найти'}
        </Button>
      </Stack>

      {mutation.isError && <Alert severity="error">{getApiErrorDetail(mutation.error)}</Alert>}
      {mutation.isSuccess && mutation.data && <CourtList courts={mutation.data} />}
    </Stack>
  )
}

import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import type { RosreestrInfo } from '../api/types'
import { getPropertyInfo, searchByAddress } from '../features/rosreestr/rosreestrApi'

type SearchType = 'cadastral' | 'address'

export function RosreestrPage() {
  const [searchType, setSearchType] = useState<SearchType>('cadastral')
  const [query, setQuery] = useState('')

  const mutation = useMutation<RosreestrInfo, ApiError, void>({
    mutationFn: () =>
      searchType === 'cadastral'
        ? getPropertyInfo(query.trim())
        : searchByAddress(query.trim()),
  })

  const isCadastral = searchType === 'cadastral'

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Росреестр</Typography>
      <Typography variant="body2" color="text.secondary">
        Поиск сведений об объекте недвижимости по кадастровому номеру или адресу.
      </Typography>

      <ToggleButtonGroup
        value={searchType}
        exclusive
        size="small"
        onChange={(_event, value) => {
          if (value !== null && value !== searchType) {
            setSearchType(value)
            mutation.reset()
          }
        }}
      >
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
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !query.trim()}
          sx={{ minWidth: 160 }}
        >
          {mutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Найти'}
        </Button>
      </Stack>

      {mutation.isError && <Alert severity="error">{getApiErrorDetail(mutation.error)}</Alert>}

      {mutation.isSuccess && mutation.data && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Результат
            </Typography>
            <Box
              component="pre"
              sx={{ overflowX: 'auto', fontSize: 12, m: 0, bgcolor: 'grey.50', p: 2, borderRadius: 1 }}
            >
              {JSON.stringify(mutation.data, null, 2)}
            </Box>
          </CardContent>
        </Card>
      )}
    </Stack>
  )
}

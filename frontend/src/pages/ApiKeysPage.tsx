import { useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import CopyAllIcon from '@mui/icons-material/CopyAll'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import type { ApiKeyAdminOut, ApiKeyCreated, ApiKeyOut, UserOut } from '../api/types'
import { useAuth } from '../features/auth/useAuth'
import { createApiKey, deleteApiKey, listApiKeys, toggleApiKey } from '../features/auth/authApi'
import { listAllApiKeys, listUsers, revokeAnyKey } from '../features/admin/adminApi'

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('ru-RU')
}

interface KeyRow {
  id: number
  name: string
  key_prefix: string
  is_active: boolean
  created_at: string | null
  last_used_at: string | null
  user_id?: number
}

function ApiKeysTable({
  keys,
  showUsername = false,
  usernameOf,
  onToggle,
  onRevoke,
  busy = false,
}: {
  keys: KeyRow[]
  showUsername?: boolean
  usernameOf?: (userId: number) => string
  onToggle?: (key: KeyRow) => void
  onRevoke?: (key: KeyRow) => void
  busy?: boolean
}) {
  if (keys.length === 0) {
    return <Alert severity="info">Ключи не найдены.</Alert>
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Название</TableCell>
            <TableCell>Префикс</TableCell>
            {showUsername && <TableCell>Логин</TableCell>}
            <TableCell>Статус</TableCell>
            <TableCell>Создан</TableCell>
            <TableCell>Использован</TableCell>
            <TableCell align="right">Действия</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {keys.map((key) => (
            <TableRow key={key.id}>
              <TableCell>{key.name}</TableCell>
              <TableCell sx={{ fontFamily: 'monospace' }}>{key.key_prefix}</TableCell>
              {showUsername && <TableCell>{usernameOf?.(key.user_id ?? 0) ?? '—'}</TableCell>}
              <TableCell>
                <Chip
                  label={key.is_active ? 'Активен' : 'Неактивен'}
                  color={key.is_active ? 'success' : 'default'}
                  size="small"
                  variant="outlined"
                />
              </TableCell>
              <TableCell>{formatDateTime(key.created_at)}</TableCell>
              <TableCell>{formatDateTime(key.last_used_at)}</TableCell>
              <TableCell align="right">
                <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                  {onToggle && (
                    <Button size="small" variant="outlined" onClick={() => onToggle(key)} disabled={busy}>
                      {key.is_active ? 'Деактивировать' : 'Активировать'}
                    </Button>
                  )}
                  {onRevoke && (
                    <Button
                      size="small"
                      color="error"
                      variant="outlined"
                      onClick={() => onRevoke(key)}
                      disabled={busy}
                    >
                      Отозвать
                    </Button>
                  )}
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

function UserApiKeys() {
  const [name, setName] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [newKey, setNewKey] = useState<string | null>(null)

  const keysQuery = useQuery<ApiKeyOut[], ApiError>({
    queryKey: ['api-keys'],
    queryFn: listApiKeys,
  })

  const createMutation = useMutation<ApiKeyCreated, ApiError, string>({
    mutationFn: (n) => createApiKey({ name: n }),
    onSuccess: (data) => {
      setNewKey(data.key)
      setName('')
      setCreateOpen(false)
      void keysQuery.refetch()
    },
  })

  const toggleMutation = useMutation<ApiKeyOut, ApiError, { id: number; isActive: boolean }>({
    mutationFn: ({ id, isActive }) => toggleApiKey(id, { is_active: isActive }),
    onSuccess: () => void keysQuery.refetch(),
  })

  const revokeMutation = useMutation<void, ApiError, number>({
    mutationFn: (id) => deleteApiKey(id),
    onSuccess: () => void keysQuery.refetch(),
  })

  const busy = createMutation.isPending || toggleMutation.isPending || revokeMutation.isPending

  const handleCopy = async () => {
    if (!newKey) return
    try {
      await navigator.clipboard.writeText(newKey)
    } catch {
      // игнорируем (например, нет доступа к clipboard)
    }
  }

  const handleRevoke = (key: KeyRow) => {
    if (window.confirm(`Отозвать ключ «${key.name}»?`)) {
      revokeMutation.mutate(key.id)
    }
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">API-ключи</Typography>
      <Typography variant="body2" color="text.secondary">
        Создание, активация/деактивация и отзыв API-ключей вашего аккаунта.
      </Typography>

      {keysQuery.isError && <Alert severity="error">{getApiErrorDetail(keysQuery.error)}</Alert>}
      {toggleMutation.isError && (
        <Alert severity="error">{getApiErrorDetail(toggleMutation.error)}</Alert>
      )}
      {revokeMutation.isError && (
        <Alert severity="error">{getApiErrorDetail(revokeMutation.error)}</Alert>
      )}

      <Box>
        <Button
          variant="contained"
          onClick={() => {
            setName('')
            setCreateOpen(true)
          }}
        >
          Создать новый API ключ
        </Button>
      </Box>

      <ApiKeysTable
        keys={keysQuery.data ?? []}
        onToggle={(key) => toggleMutation.mutate({ id: key.id, isActive: !key.is_active })}
        onRevoke={handleRevoke}
        busy={busy}
      />

      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        maxWidth="xs"
        fullWidth
        slotProps={{ backdrop: { sx: { backgroundColor: 'rgba(0, 0, 0, 0.32)' } } }}
      >
        <DialogTitle>Создать новый API ключ</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Название ключа"
            value={name}
            onChange={(event) => setName(event.target.value)}
            sx={{ mt: 1 }}
          />
          {createMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {getApiErrorDetail(createMutation.error)}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Отмена</Button>
          <Button
            variant="contained"
            onClick={() => createMutation.mutate(name.trim())}
            disabled={createMutation.isPending || !name.trim()}
          >
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!newKey} onClose={() => setNewKey(null)} maxWidth="sm" fullWidth>
        <DialogTitle
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <Typography variant="h6" component="span">
            Ключ создан
          </Typography>
          <IconButton onClick={() => setNewKey(null)} size="small" aria-label="Закрыть">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Сохраните ключ — он показывается только один раз.
          </Alert>
          <Stack direction="row" spacing={1}>
            <TextField fullWidth value={newKey ?? ''} slotProps={{ input: { readOnly: true } }} />
            <Button variant="outlined" startIcon={<CopyAllIcon />} onClick={handleCopy}>
              Копировать
            </Button>
          </Stack>
        </DialogContent>
      </Dialog>
    </Stack>
  )
}

function AdminApiKeys() {
  const [search, setSearch] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  const keysQuery = useQuery<ApiKeyAdminOut[], ApiError>({
    queryKey: ['admin', 'api-keys'],
    queryFn: listAllApiKeys,
  })

  const usersQuery = useQuery<UserOut[], ApiError>({
    queryKey: ['admin', 'users'],
    queryFn: listUsers,
  })

  const revokeMutation = useMutation<void, ApiError, number>({
    mutationFn: (id) => revokeAnyKey(id),
    onSuccess: () => void keysQuery.refetch(),
  })

  const filtered = useMemo(() => {
    const users = usersQuery.data ?? []
    const usernameMap = new Map(users.map((u) => [u.id, u.username]))
    let keys = keysQuery.data ?? []

    const s = search.trim().toLowerCase()
    if (s) {
      keys = keys.filter((key) =>
        (usernameMap.get(key.user_id) ?? '').toLowerCase().includes(s),
      )
    }

    if (dateFrom) {
      const from = new Date(dateFrom).getTime()
      keys = keys.filter((key) => key.created_at && new Date(key.created_at).getTime() >= from)
    }

    if (dateTo) {
      const to = new Date(dateTo)
      to.setHours(23, 59, 59, 999)
      keys = keys.filter((key) => key.created_at && new Date(key.created_at).getTime() <= to.getTime())
    }

    return keys
  }, [keysQuery.data, usersQuery.data, search, dateFrom, dateTo])

  const paginated = filtered.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  const usernameOf = (userId: number) =>
    usersQuery.data?.find((u) => u.id === userId)?.username ?? '—'

  const handleRevoke = (key: KeyRow) => {
    if (window.confirm(`Отозвать ключ «${key.name}»?`)) {
      revokeMutation.mutate(key.id)
    }
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">API-ключи (администратор)</Typography>
      <Typography variant="body2" color="text.secondary">
        Все ключи пользователей с фильтрацией.
      </Typography>

      {(keysQuery.isError || usersQuery.isError) && (
        <Alert severity="error">
          {getApiErrorDetail(keysQuery.error ?? usersQuery.error)}
        </Alert>
      )}
      {revokeMutation.isError && (
        <Alert severity="error">{getApiErrorDetail(revokeMutation.error)}</Alert>
      )}

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'flex-end' }}>
        <TextField
          label="Поиск по логину"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value)
            setPage(0)
          }}
          sx={{ minWidth: 220 }}
        />
        <TextField
          label="С даты"
          type="date"
          value={dateFrom}
          onChange={(event) => {
            setDateFrom(event.target.value)
            setPage(0)
          }}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <TextField
          label="По дату"
          type="date"
          value={dateTo}
          onChange={(event) => {
            setDateTo(event.target.value)
            setPage(0)
          }}
          slotProps={{ inputLabel: { shrink: true } }}
        />
      </Stack>

      <ApiKeysTable
        keys={paginated}
        showUsername
        usernameOf={usernameOf}
        onRevoke={handleRevoke}
        busy={revokeMutation.isPending}
      />

      <TablePagination
        component="div"
        count={filtered.length}
        page={page}
        onPageChange={(_event, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10))
          setPage(0)
        }}
        rowsPerPageOptions={[10, 25, 50, 100]}
        labelRowsPerPage="Записей на странице:"
        labelDisplayedRows={({ from, to, count }) => `${from}–${to} из ${count}`}
      />
    </Stack>
  )
}

export function ApiKeysPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return isAdmin ? <AdminApiKeys /> : <UserApiKeys />
}

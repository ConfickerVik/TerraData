import { useState } from 'react'
import {
  Alert,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import type { UserAdminUpdate, UserOut } from '../api/types'
import { useAuth } from '../features/auth/useAuth'
import { deleteUser, listUsers, updateUser } from '../features/admin/adminApi'

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('ru-RU')
}

function EditUserDialog({
  user,
  onClose,
  onSaved,
}: {
  user: UserOut
  onClose: () => void
  onSaved: () => void
}) {
  const [role, setRole] = useState(user.role)
  const [isActive, setIsActive] = useState(user.is_active)
  const [limitText, setLimitText] = useState(
    user.request_limit != null ? String(user.request_limit) : '',
  )

  const mutation = useMutation<UserOut, ApiError, UserAdminUpdate>({
    mutationFn: (payload) => updateUser(user.id, payload),
    onSuccess: () => {
      onSaved()
      onClose()
    },
  })

  const handleSave = () => {
    const payload: UserAdminUpdate = { role, is_active: isActive }
    const trimmed = limitText.trim()
    if (trimmed !== '') {
      payload.request_limit = Number(trimmed)
    }
    mutation.mutate(payload)
  }

  return (
    <Dialog open onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Редактировать пользователя</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Логин: {user.username}
          </Typography>

          <FormControl fullWidth>
            <InputLabel id="role-label">Роль</InputLabel>
            <Select
              labelId="role-label"
              label="Роль"
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              <MenuItem value="user">Пользователь</MenuItem>
              <MenuItem value="admin">Администратор</MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch checked={isActive} onChange={(_event, checked) => setIsActive(checked)} />
            }
            label="Активен"
          />

          <TextField
            label="Лимит запросов (пусто — не изменять)"
            type="number"
            value={limitText}
            onChange={(event) => setLimitText(event.target.value)}
            fullWidth
          />

          {mutation.isError && (
            <Alert severity="error">{getApiErrorDetail(mutation.error)}</Alert>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button onClick={handleSave} disabled={mutation.isPending}>
          Сохранить
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export function AdminPage() {
  const { user: currentUser } = useAuth()
  const [editingUser, setEditingUser] = useState<UserOut | null>(null)

  const usersQuery = useQuery<UserOut[], ApiError>({
    queryKey: ['admin', 'users'],
    queryFn: listUsers,
  })

  const deleteMutation = useMutation<void, ApiError, number>({
    mutationFn: (id) => deleteUser(id),
    onSuccess: () => void usersQuery.refetch(),
  })

  const handleDelete = (user: UserOut) => {
    if (window.confirm(`Удалить пользователя «${user.username}»?`)) {
      deleteMutation.mutate(user.id)
    }
  }

  const users = usersQuery.data ?? []

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Администрирование</Typography>
      <Typography variant="body2" color="text.secondary">
        Управление пользователями: роли, блокировка, лимиты запросов.
      </Typography>

      {usersQuery.isError && <Alert severity="error">{getApiErrorDetail(usersQuery.error)}</Alert>}
      {deleteMutation.isError && (
        <Alert severity="error">{getApiErrorDetail(deleteMutation.error)}</Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Логин</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Роль</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Лимит</TableCell>
              <TableCell>Создан</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => {
              const isSelf = user.id === currentUser?.id
              return (
                <TableRow key={user.id}>
                  <TableCell>{user.id}</TableCell>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.email ?? '—'}</TableCell>
                  <TableCell>
                    <Chip
                      label={user.role === 'admin' ? 'Админ' : 'Пользователь'}
                      size="small"
                      variant="outlined"
                      color={user.role === 'admin' ? 'primary' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Активен' : 'Заблокирован'}
                      size="small"
                      variant="outlined"
                      color={user.is_active ? 'success' : 'error'}
                    />
                  </TableCell>
                  <TableCell>{user.request_limit != null ? user.request_limit : '—'}</TableCell>
                  <TableCell>{formatDateTime(user.created_at)}</TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                      <Button size="small" variant="outlined" onClick={() => setEditingUser(user)}>
                        Изменить
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        variant="outlined"
                        onClick={() => handleDelete(user)}
                        disabled={isSelf}
                      >
                        Удалить
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {editingUser && (
        <EditUserDialog
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSaved={() => void usersQuery.refetch()}
        />
      )}
    </Stack>
  )
}

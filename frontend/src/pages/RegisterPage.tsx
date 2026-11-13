import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Stack, TextField, Typography } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import { useAuth } from '../features/auth/useAuth'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const mutation = useMutation<void, ApiError, void>({
    mutationFn: () => register(username, password, email || undefined),
    onSuccess: () => navigate('/login'),
  })

  return (
    <Stack spacing={2}>
      <Typography variant="h5" align="center">
        Регистрация
      </Typography>
      <TextField
        label="Имя пользователя"
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        fullWidth
        autoFocus
        helperText="Минимум 3 символа"
      />
      <TextField
        label="Email (необязательно)"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        fullWidth
      />
      <TextField
        label="Пароль"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        fullWidth
        helperText="Минимум 8 символов"
      />
      {mutation.isError && <Alert severity="error">{getApiErrorDetail(mutation.error)}</Alert>}
      {mutation.isSuccess && (
        <Alert severity="success">Аккаунт создан, теперь войдите.</Alert>
      )}
      <Button
        variant="contained"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || username.length < 3 || password.length < 8}
        fullWidth
      >
        {mutation.isPending ? 'Создание…' : 'Зарегистрироваться'}
      </Button>
      <Button variant="text" onClick={() => navigate('/login')}>
        Уже есть аккаунт? Войти
      </Button>
    </Stack>
  )
}
